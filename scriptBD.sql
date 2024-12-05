create database emprego;

use emprego;

create table empresa(
    id_empresa int primary key auto_increment,
    nome_empresa varchar(100) not null,
    cnpj char(14) unique not null,
    telefone char(11) not null,
    email varchar(100) unique not null,
    senha varchar(30) not null,
    status enum('ativa', 'inativa') default 'ativa' not null
);

create table vaga(
    id_vaga int primary key auto_increment,
    titulo varchar(100) not null,
    descricao varchar(100) not null,
    formato enum('Presencial', 'Híbrido', 'Remoto') not null,
    tipo enum('CLT', 'PJ') not null,
    local varchar(100),
    salario varchar(10),
    id_empresa int not null,
    status enum('ativa', 'inativa') default 'ativa' not null,
    foreign key (id_empresa) references empresa (id_empresa)
);

create table candidato(
    id_candidato int primary key auto_increment,
    nome varchar(100) not null,
    email varchar(100) unique not null,
    telefone char(11) not null,
    curriculo varchar(50) not null,
    id_vaga int not null,
    id_empresa int not null,
    data_upload timestamp default current_timestamp,
    foreign key (id_vaga) references vaga (id_vaga),
    foreign key (id_empresa) references empresa (id_empresa)
);

DELIMITER $$

CREATE TRIGGER delete_vaga
BEFORE DELETE ON empresa
FOR EACH ROW
BEGIN
    DELETE FROM vaga WHERE id_empresa = OLD.id_empresa;
END $$

DELIMITER ;



DELIMITER $$

CREATE TRIGGER delete_candidato
before DELETE ON vaga
FOR EACH ROW
BEGIN
    DELETE FROM candidato WHERE id_empresa = OLD.id_empresa;

END $$

DELIMITER ;
