-- Migration script to add type field to existing player table
-- Run this if you already have the player table without the type field

-- Add type column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'player' AND column_name = 'type'
    ) THEN
        -- Add the column with default value
        ALTER TABLE public.player
        ADD COLUMN type character varying(10) NOT NULL DEFAULT 'human';

        -- Add constraint
        ALTER TABLE public.player
        ADD CONSTRAINT player_type_check CHECK (type IN ('human', 'ai'));

        -- Create index
        CREATE INDEX idx_player_type ON public.player(type);

        -- Update existing AI players (those with IDs starting with 'T-')
        UPDATE public.player SET type = 'ai' WHERE id LIKE 'T-%';

        RAISE NOTICE 'Successfully added type column to player table';
    ELSE
        RAISE NOTICE 'Type column already exists';
    END IF;
END $$;
