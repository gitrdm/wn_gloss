-- EXAMPLE DUCKDB QUERY: King Definitions with Related Synsets
-- This query finds all definitions of "king" and shows synsets for words used in those definitions

-- Step 1: Get all "king" synsets and their definitions
WITH king_definitions AS (
    SELECT 
        synset_id,
        pos,
        gloss.original_text as definition,
        list_transform(terms, x -> x.term) as all_terms
    FROM read_json_auto('/home/rdmerrio/lgits/wn_gloss/old_gloss/json_file/wordnet.jsonl') w
    WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
),

-- Step 2: Extract key definition words for the most common sense of king (male sovereign)
key_definition_words AS (
    SELECT ['male', 'sovereign', 'ruler', 'kingdom', 'chess', 'piece', 'competitor', 'powerful', 'businessman'] as words
),

-- Step 3: Find synsets that contain these definition words
related_synsets AS (
    SELECT DISTINCT
        w.synset_id,
        w.pos,
        list_transform(w.terms, x -> x.term) as terms,
        w.gloss.original_text as definition,
        -- Find which key words this synset contains
        list_filter(
            (SELECT words FROM key_definition_words), 
            word -> list_contains(list_transform(w.terms, x -> x.term), word)
        ) as matching_words
    FROM read_json_auto('/home/rdmerrio/lgits/wn_gloss/old_gloss/json_file/wordnet.jsonl') w
    WHERE EXISTS (
        SELECT 1 
        FROM unnest((SELECT words FROM key_definition_words)) as key_word
        WHERE list_contains(list_transform(w.terms, x -> x.term), key_word)
    )
)

-- Final result: Show king definitions and related synsets
SELECT 
    'KING_DEFINITION' as type,
    synset_id,
    pos,
    definition,
    all_terms as terms,
    NULL as matching_words
FROM king_definitions

UNION ALL

SELECT 
    'RELATED_SYNSET' as type,
    synset_id,
    pos,
    definition,
    terms,
    matching_words
FROM related_synsets
WHERE len(matching_words) > 0

ORDER BY type DESC, synset_id;
