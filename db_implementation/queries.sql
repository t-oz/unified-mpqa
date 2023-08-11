-- working query
select * from
    (select a.*, sen.sentence_id, file, file_sentence_id, sentence,
       m.token_id, m.token_id, token_text, token_offset_start, token_offset_end,
       s.source_id, s.source_id, parent_source_id, nesting_level, source from sentences sen
join mentions m on sen.sentence_id = m.sentence_id
join sources s on m.token_id = s.token_id
join attitudes a on s.source_id = a.source_id) source_data

join

    (select a.*, sen.sentence_id, file, file_sentence_id, sentence,
       m.token_id, m.token_id, token_text, token_offset_start, token_offset_end from sentences sen
join mentions m on sen.sentence_id = m.sentence_id
join attitudes a on a.anchor_token_id = m.token_id) anchor_data on source_data.attitude_id = anchor_data.attitude_id
