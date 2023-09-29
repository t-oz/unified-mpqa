select a.label_type, a.intensity, a.polarity, s2.source_id, s2.source source_text, s2.nesting_level,
       (select source from sources where source_id = s2.parent_source_id) parent_source,
       (select token_text from mentions where token_id = a.anchor_token_id) anchor_text,
       m.token_text target_text, s.sentence from attitudes a
join mentions m on a.target_token_id = m.token_id
join sentences s on m.sentence_id = s.sentence_id
left join sources s2 on a.source_id = s2.source_id;