from flask import Flask, render_template, request, redirect, session, send_from_directory
from mysql.connector import Error
from config import *
from db_functions import *
import os


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'uploads/'



@app.route('/')
def index():
    if session:
        if 'adm' in session:
            login = 'adm'
        else:
            login = 'empresa'
    else:
        login = False

    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa 
        FROM vaga 
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa
        WHERE vaga.status = 'ativa'
        ORDER BY vaga.id_vaga DESC;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL)
        vagas = cursor.fetchall()
        return render_template('index.html', vagas=vagas, login=login)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)


# ROTA DA PÁGINA DE LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session:
        if 'adm' in session:
            return redirect('/adm')
        else:
            return redirect('/empresa')

    if request.method == 'GET': 
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        if not email or not senha: 
            erro = "Os campos precisam estar preenchidos!"
            return render_template('login.html', msg_erro=erro)

        if email == MASTER_EMAIL and senha == MASTER_PASSWORD:
            session['adm'] = True
            return redirect('/adm')

        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE email = %s AND senha = %s'
            cursor.execute(comandoSQL, (email, senha))
            empresa = cursor.fetchone()

            if not empresa:
                return render_template('login.html', msgerro='E-mail e/ou senha estão errados!')

            if empresa['status'] == 'inativa':
                return render_template('login.html', msgerro='Empresa desativada! Procure o administrador!')

            session['id_empresa'] = empresa['id_empresa']
            session['nome_empresa'] = empresa['nome_empresa']
            return redirect('/empresa')
        
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA DA PÁGINA DO ADMIN
@app.route('/adm')
def adm():
    #Se não houver sessão ativa
    if not session:
        return redirect('/login')
    #Se não for o administrador
    if not 'adm' in session:
        return redirect('/empresa')
  
    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM Empresa WHERE status = "ativa"'
        cursor.execute(comandoSQL)
        empresas_ativas = cursor.fetchall()

        comandoSQL = 'SELECT * FROM Empresa WHERE status = "inativa"'
        cursor.execute(comandoSQL)
        empresas_inativas = cursor.fetchall()

        return render_template('adm.html', empresas_ativas=empresas_ativas, empresas_inativas=empresas_inativas)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)


@app.route('/cadastrar_empresa', methods =['GET','POST'])
def cadastrar_empresas():
    if not session:
        return redirect('/login')
    if not 'adm' in session:
        return redirect('/empresa')

    if request.method == 'GET':
        return render_template('cadastrar_empresa.html')

    if request.method == 'POST':
        nome_empresa = request.form['nome_empresa']
        cnpj = limpar_input(request.form['cnpj'])
        telefone = limpar_input(request.form['telefone'])
        email = request.form['email']
        senha = request.form['senha']

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'INSERT INTO empresa  (nome_empresa, cnpj, telefone, email, senha) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(comandoSQL, (nome_empresa, cnpj, telefone, email, senha))
        conexao.commit()
        return redirect('/adm')
    except Error as erro:
        if erro.errno == 1062:
            return render_template('cadastrar_empresa.html')
        else:
            return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)


@app.route('/editar_empresa/<int:id_empresa>', methods=['GET','POST'])
def editar_empresa(id_empresa):
    if not session:
        return redirect('/login')

    if not session['adm']:
        return redirect('/login')

    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE id_empresa = %s'
            cursor.execute(comandoSQL, (id_empresa,))
            empresa = cursor.fetchone()
            return render_template('editar_empresa.html',empresa=empresa)
        except Error as erro:
            return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    if request.method == 'POST':
        nome_empresa = request.form['nome_empresa']
        cnpj = limpar_input(request.form['cnpj'])
        telefone = limpar_input(request.form['telefone'])
        email = request.form['email']
        senha = request.form['senha']
    
    if not nome_empresa or not cnpj or not telefone or not email or not senha:
        return render_template('editar_empresa.html', msg_erro='Preencha todos os campos')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        update empresa 
        set nome_empresa = %s, cnpj = %s, telefone = %s, email = %s, senha = %s
        where id_empresa = %s;
        '''
        cursor.execute(comandoSQL, (nome_empresa, cnpj, telefone, email, senha, id_empresa))
        conexao.commit()
        return redirect('/adm')
    except Error as erro:
        if erro.errno == 1062:
            return render_template('editar_empresa.html',msg_erro="Esse email já existe", empresa=empresa)
        else:
            return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/status_empresa/<int:id_empresa>')
def status(id_empresa):
    if not session:
        return redirect('/login')
    if not session['adm']:
        return redirect('/login')
    
    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM empresa WHERE id_empresa = %s'
        cursor.execute(comandoSQL, (id_empresa,))
        status_empresa = cursor.fetchone()
        if status_empresa['status'] == 'ativa':
            novo_status = 'inativa'
        else:
            novo_status = 'ativa'
        
        comandoSQL = 'UPDATE empresa SET status=%s WHERE id_empresa = %s'
        cursor.execute(comandoSQL, (novo_status, id_empresa))
        conexao.commit()

        # Se a empresa estiver sendo desativada, as vagas também serão
        if novo_status == 'inativa':
            comandoSQL = 'UPDATE vaga SET status = %s WHERE id_empresa = %s'
            cursor.execute(comandoSQL, (novo_status,id_empresa))
            conexao.commit()
        return redirect('/adm')
    except Error as erro:  
        return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/excluir_empresa/<int:id_empresa>')
def excluir_empresa(id_empresa):
    if not session:
        return redirect('/login')
    if not session['adm']:
        return redirect('/login')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'delete from vaga where id_empresa=%s'
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()
        
        comandoSQL = 'delete from empresa where id_empresa=%s'
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()
        return redirect('/adm')
    except Error as erro:
        return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)

#ROTA DA PÁGINA DE GESTÃO DAS EMPRESAS
@app.route('/empresa')
def empresa():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    id_empresa = session['id_empresa']
    nome_empresa = session['nome_empresa']

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM vaga WHERE id_empresa = %s AND status = "ativa" ORDER BY id_vaga DESC'
        cursor.execute(comandoSQL, (id_empresa,))
        vagas_ativas = cursor.fetchall()
        
        comandoSQL = 'SELECT * FROM vaga WHERE id_empresa = %s AND status = "inativa" ORDER BY id_vaga DESC'
        cursor.execute(comandoSQL, (id_empresa,))
        vagas_inativas = cursor.fetchall()

        return render_template('empresa.html', nome_empresa=nome_empresa, vagas_ativas=vagas_ativas, vagas_inativas=vagas_inativas)         
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/cadastrar_vaga', methods=['POST','GET'])
def cadadastrarvaga():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')
    
    if request.method == 'GET':
        return render_template('cadastrar_vaga.html')
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = ''
        local = request.form['local']
        salario = ''
        salario = request.form['salario']
        id_empresa = session['id_empresa']
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            INSERT INTO Vaga (titulo, descricao, formato, tipo, local, salario, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, id_empresa))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route('/editar_vaga/<int:id_vaga>', methods=['GET','POST'])
def editarvaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM vaga WHERE id_vaga = %s;'
            cursor.execute(comandoSQL, (id_vaga,))
            vaga = cursor.fetchone()
            return render_template('editar_vaga.html', vaga=vaga)
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = request.form['local']
        salario = request.form['salario']

        if not titulo or not descricao or not formato or not tipo:
            return redirect('/empresa')
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            UPDATE vaga SET titulo=%s, descricao=%s, formato=%s, tipo=%s, local=%s, salario=%s
            WHERE id_vaga = %s;
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, id_vaga))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao) 

#ROTA PARA ALTERAR O STATUS DA VAGA
@app.route("/status_vaga/<int:id_vaga>")
def statusvaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM vaga WHERE id_vaga = %s;'
        cursor.execute(comandoSQL, (id_vaga,))
        vaga = cursor.fetchone()
        if vaga['status'] == 'ativa':
            status = 'inativa'
        else:
            status = 'ativa'

        comandoSQL = 'UPDATE vaga SET status = %s WHERE id_vaga = %s'
        cursor.execute(comandoSQL, (status, id_vaga))
        conexao.commit()
        return redirect('/empresa')
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)
        
@app.route("/excluir_vaga/<int:id_vaga>")
def excluirvaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'delete from vaga where id_vaga = %s'
        cursor.execute(comandoSQL, (id_vaga,))
        conexao.commit()
        return redirect('/empresa')             
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)    

#ROTA PARA VER DETALHES DA VAGA
@app.route('/sobre_vaga/<int:id_vaga>')
def sobre_vaga(id_vaga):
    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa 
        FROM vaga 
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa 
        WHERE vaga.id_vaga = %s;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (id_vaga,))
        vaga = cursor.fetchone()

        if not vaga:
            return redirect('/')
        return render_template('sobre_vaga.html', vaga=vaga)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)    

@app.route('/procurar_vagas')
def procurar_vagas():
    try:
        word = request.args.get('word')  
        comandoSQL = '''    
        select vaga.*, empresa.nome_empresa 
        from vaga 
        join empresa on vaga.id_empresa = empresa.id_empresa
        where vaga.titulo like %s and vaga.status = 'ativa'
        order by vaga.id_vaga desc;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (f"%{word}%",)) 
        vagas_buscadas = cursor.fetchall()
        return render_template('buscar_vaga.html', vagas=vagas_buscadas, word=word)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)   

@app.route('/curriculo/<int:id_vaga>', methods=['POST', 'GET'])
def curriculo(id_vaga):
    comandoSQL = '''
    SELECT vaga.*, empresa.nome_empresa 
    FROM vaga 
    JOIN empresa ON vaga.id_empresa = empresa.id_empresa 
    WHERE vaga.id_vaga = %s;
    '''
    
    conexao, cursor = conectar_db()
    cursor.execute(comandoSQL, (id_vaga,))
    vaga = cursor.fetchone()
    if request.method == 'GET':
        try:

            return render_template('curriculo.html', vaga=vaga)

        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    if request.method == 'POST':
        try:
            nome = request.form['nome']
            telefone = limpar_input(request.form['telefone'])
            email = request.form['email']
            file = request.files['file']
            

            if file.filename == '':
                msg = "Nenhum arquivo selecionado!"
                return render_template('curriculo.html', msg=msg,)

            nome_arquivo = f"id{id_vaga}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))

            conexao, cursor = conectar_db()
            comandoSQL = "INSERT INTO candidato (nome, email, telefone, curriculo, id_vaga, id_empresa) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(comandoSQL, (nome, email, telefone, nome_arquivo, id_vaga, vaga['id_empresa']))
            conexao.commit()

            return redirect('/')

        except mysql.connector.Error as erro:
            return render_template('curriculo.html', msg=f"Erro de BD {erro}")
        except Exception as erro:
            return render_template('curriculo.html', msg=f"Erro de Backend {erro}")
        finally:
            encerrar_db(cursor, conexao)

@app.route('/ver_curriculos/<int:id_vaga>')
def ver_curriculos(id_vaga):
    if request.method == 'GET':
        try:
            comandoSQL = '''
        SELECT candidato.*, vaga.*
        FROM candidato 
        JOIN vaga ON candidato.id_vaga = vaga.id_vaga
        WHERE candidato.id_vaga = %s
        ORDER BY candidato.id_candidato DESC;
            '''         
            conexao, cursor = conectar_db()
            cursor.execute(comandoSQL, (id_vaga, ))
            candidatos = cursor.fetchall()
            return render_template('ver_curriculos.html', candidatos=candidatos)
        except mysql.connector.Error as erro:
            return render_template('curriculo.html', msg=f"Erro de BD {erro}")
        except Exception as erro:
            return render_template('curriculo.html', msg=f"Erro de Backend {erro}")
        finally:
            encerrar_db(cursor, conexao)    
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)                
            
@app.route('/ver/<filename>')
def ver(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
            
@app.route('/delete/<filename>/<int:id_vaga>')
def delete_file(filename, id_vaga):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(file_path)

        conexao, cursor = conectar_db()
        comandoSQL = "DELETE FROM candidato WHERE curriculo = %s"
        cursor.execute(comandoSQL, (filename,))
        conexao.commit()

        return redirect(f'/ver_curriculos/{id_vaga}')
    except mysql.connector.Error as erro:
        return f"Erro de banco de Dados: {erro}"
    except Exception as erro:
        return f"Erro de back-end: {erro}"
    finally:
        encerrar_db(conexao, cursor)    
        
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)