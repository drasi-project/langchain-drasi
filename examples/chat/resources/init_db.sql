CREATE TABLE IF NOT EXISTS public."Freezer"
(
    id integer NOT NULL,
    temp integer NOT NULL,    
    CONSTRAINT "Freezer_pkey" PRIMARY KEY (id)
);

INSERT INTO public."Freezer" (id, temp) VALUES
    (1, 22),
    (2, 35),
    (3, 18);