SET lock_timeout = '5s';
SET statement_timeout = '30s';
ALTER TABLE student ADD COLUMN IF NOT EXISTS email VARCHAR(120);
