This is an example project on the usage of the Drasi LangGraph library.

It consists of a an interactive game, where players join via a web portal, enter their name and a player is created. Players are all tracked in a postgresql table with the following schema:

CREATE TABLE IF NOT EXISTS public.player
(
    id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    x integer NOT NULL,
    y integer NOT NULL,
    type character varying(10) NOT NULL DEFAULT 'human',
    CONSTRAINT player_pkey PRIMARY KEY (id),
    CONSTRAINT player_type_check CHECK (type IN ('human', 'ai'))
)

The "id" field is the name that the player enters, the x and y fields are the coordinates in a 2D space that is 32 x 64.

The space has walls and is as follows:

-----------------------------------------------------------------
|            |               |                    |             |
|                            |                                  |
|            |               |                    |             |
|------------|----  ---------|--------  ----------|-------------|
|            |               |                    |             |
|            |                                    |             |
|            |               |                                  |
|            |               |                    |             |
|--------  --|----  ---------|-----------------  -|-----  ------|
|                                                               |
|                                                               |
|                                                               |
|                                                               |
|---------------------------------------------------------------|

When a player enters the game, a random position is chosen that is not a wall.
This is written to the postgres table.
The player sees themself as a green marker on the map and can move in up, down, left or right using the arrow keys, this in turn updates the postgres table. They cannot walk through walls. They see other players that have joined as blue markers.

There are also 3 AI players, these are terminators, and when they touch a player, the player is out of the game and the record is deleted from the database.
These AI players are driven by an agentic workflow powered by LangGraph.
The positions of the players are not visible to these agents, except they have access to the Drasi query tool (connection details provided my env variables), which will provide a set of queries that can feed them information in an async manner. The agents should discover these queries and subscribe to them in order to get visibility of player movements. When an async notification is recieved it must be stored in the agents memory to help it track the players movements. The agents can move once every second and they must try to eliminate the players.
The terminator agents are displayed as red markers on each players UI.



