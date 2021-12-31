
BEGIN;

CREATE TABLE webs (
    id integer NOT NULL,
    web text NOT NULL
);

CREATE TABLE regularexpressions (
    id integer NOT NULL,
    namebehav text NOT NULL,
    regexbehav text NOT NULL
);

INSERT INTO webs(id, web) VALUES (1, 'https://en.wikipedia.org/wiki/');


INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (1, 'TranslatorBehav', '^(H|h)ow[a-zA-Z_ ]*say[a-zA-Z_ ]*(S|s)panish\s+');
INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (2, 'CalculateBehav', '^(H|h)ow\s+much\s+is\s+(\d+["+""*""-""/""**"])+');
INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (3, 'CalculateBehav2', '^(H|h)ow\s*much\s*is\s*');
INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (4, 'TimeBehav', '^(W|w)hat[a-zA-Z_ ]*time[a-zA-Z_ ]*\?');
INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (5, 'CreateFileBehav', '^(C|c)reate\s+file\s+');
INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (6, 'PersonBehav', '^(T|t)ell\s+(me|)\s+about\s+');
INSERT INTO regularexpressions(id, namebehav, regexbehav) VALUES (7, 'EndBehav', '^((B|b)ye|(S|s)ee\s+you|(E|e)xit)');

COMMIT;

ANALYZE webs;
ANALYZE regularexpressions;