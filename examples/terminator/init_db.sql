-- Terminator Game Database Schema
-- This script initializes the PostgreSQL database for the terminator game

-- Drop table if exists
DROP TABLE IF EXISTS public.player;

-- Create player table
CREATE TABLE IF NOT EXISTS public.player
(
    id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    x integer NOT NULL,
    y integer NOT NULL,
    type character varying(10) NOT NULL DEFAULT 'human',
    CONSTRAINT player_pkey PRIMARY KEY (id),
    CONSTRAINT player_type_check CHECK (type IN ('human', 'ai'))
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_position ON public.player(x, y);
CREATE INDEX IF NOT EXISTS idx_player_type ON public.player(type);

-- Grant permissions (adjust as needed)
ALTER TABLE public.player OWNER TO postgres;
