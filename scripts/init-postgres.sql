-- Clinic Atlas: Idempotent FTS configuration for medical thesaurus
-- This script runs via docker-entrypoint-initdb.d on first volume init.
-- The Alembic migration also creates these idempotently for non-Docker environments.
--
-- If config/medical_thesaurus.ths changes after the Postgres volume exists:
-- 1. Restart the Postgres container to reload the thesaurus dictionary
-- 2. Call POST /api/reindex to regenerate tsvector values

-- Create thesaurus dictionary for medical abbreviation expansion
-- DictFile references the .ths file without extension, relative to tsearch_data/
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_ts_dict WHERE dictname = 'medical_thesaurus') THEN
    EXECUTE 'CREATE TEXT SEARCH DICTIONARY medical_thesaurus (
      TEMPLATE = thesaurus,
      DictFile = medical_thesaurus,
      Dictionary = english_stem
    )';
  END IF;
END $$;

-- Create custom text search configuration based on English
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'medical') THEN
    CREATE TEXT SEARCH CONFIGURATION medical (COPY = english);
    ALTER TEXT SEARCH CONFIGURATION medical
      ALTER MAPPING FOR asciiword, asciihword, hword_asciipart
      WITH medical_thesaurus, english_stem;
  END IF;
END $$;
