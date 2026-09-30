-- Manual SQL*Plus/SQLcl bootstrap, run as an administrator in the target PDB.
-- This is not an application schema migration; phase 4 adds versioned migrations.
-- Credentials are entered at runtime, never committed. Use a development account.
SET VERIFY OFF
SET ECHO OFF
ACCEPT wiki_password CHAR PROMPT 'Password for the genai development user: ' HIDE
CREATE USER genai IDENTIFIED BY "&wiki_password";
UNDEFINE wiki_password
GRANT CREATE SESSION, CREATE TABLE TO genai;
ALTER USER genai DEFAULT TABLESPACE USERS QUOTA 100M ON USERS;
