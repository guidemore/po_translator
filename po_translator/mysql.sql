Create DATABASE IF NOT EXISTS po_trans CHARACTER SET utf8;
CREATE USER 'potrans_user'@'localhost' IDENTIFIED BY 'potrans_user';
GRANT ALL PRIVILEGES ON po_trans.* TO 'potrans_user'@'localhost';

alter table potr_set_list CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
