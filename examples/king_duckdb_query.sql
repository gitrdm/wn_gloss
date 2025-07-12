-- =====================================================================
-- DUCKDB QUERY EXAMPLE: King Definitions with Related Synsets
-- =====================================================================
-- This query demonstrates how to find definitions of a word ("king") 
-- and then find synsets for the words used in those definitions.
-- 
-- Usage: Run this in DuckDB CLI or Python script
-- =====================================================================

-- STEP 1: Find all synsets containing "king" as a term
SELECT 
    '🤴 KING SYNSETS' as section,
    synset_id,
    pos,
    gloss.original_text as definition
FROM read_json_auto('/home/rdmerrio/lgits/wn_gloss/old_gloss/json_file/wordnet.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
ORDER BY synset_id

UNION ALL

-- STEP 2: Find synsets for key words used in king definitions
-- (Focus on the most common sense: "male sovereign; ruler of a kingdom")
SELECT 
    '👑 RELATED SYNSETS FOR: ' || related_word as section,
    synset_id,
    pos,
    gloss.original_text as definition
FROM (
    -- Define the key words we want to look up
    SELECT unnest(['male', 'sovereign', 'ruler', 'kingdom']) as related_word
) key_words
CROSS JOIN read_json_auto('/home/rdmerrio/lgits/wn_gloss/old_gloss/json_file/wordnet.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), related_word)
  AND rowid % 3 = 0  -- Sample every 3rd result to keep output manageable
ORDER BY section, synset_id;

-- =====================================================================
-- ALTERNATIVE: Simplified version for specific analysis
-- =====================================================================

/*
-- Just get king definitions:
SELECT synset_id, pos, gloss.original_text as definition
FROM read_json_auto('/path/to/wordnet.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'king');

-- Just get synsets for a specific definition word:
SELECT synset_id, pos, gloss.original_text as definition
FROM read_json_auto('/path/to/wordnet.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'sovereign')
LIMIT 5;

-- Combined query to see relationships:
WITH king_synsets AS (
    SELECT synset_id, gloss.original_text as def
    FROM read_json_auto('/path/to/wordnet.jsonl') w
    WHERE list_contains(list_transform(w.terms, x -> x.term), 'king')
    AND synset_id = 'n10231515'  -- male sovereign sense
)
SELECT 
    k.synset_id as king_synset,
    k.def as king_definition,
    w.synset_id as related_synset,
    list_transform(w.terms, x -> x.term)[1] as related_term,
    w.gloss.original_text as related_definition
FROM king_synsets k
CROSS JOIN read_json_auto('/path/to/wordnet.jsonl') w
WHERE list_contains(list_transform(w.terms, x -> x.term), 'male')
   OR list_contains(list_transform(w.terms, x -> x.term), 'sovereign')
LIMIT 10;
*/
