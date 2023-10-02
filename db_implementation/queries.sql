select s.file, a.label_type, a.intensity, a.polarity,
       s2.source source_text, m2.token_text, m2.token_offset_start source_start,
       m2.token_offset_end source_end, s2.nesting_level,
       (select source from sources where source_id = s2.parent_source_id) parent_source,
       m3.token_text anchor_text, m3.token_offset_start anchor_start, m3.token_offset_end anchor_end,
       m.token_text target_text, m.token_offset_start target_start, m.token_offset_end target_end,
       s.sentence from attitudes a
join mentions m on a.target_token_id = m.token_id
join sentences s on m.sentence_id = s.sentence_id
join sources s2 on a.source_id = s2.source_id
join mentions m2 on s2.token_id = m2.token_id
join mentions m3 on a.anchor_token_id = m3.token_id;