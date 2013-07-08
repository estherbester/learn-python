drop table if exists rankings;

create table rankings (
	id integer primary key autoincrement,
	name text,
    title text,
	ranking integer not null
);
