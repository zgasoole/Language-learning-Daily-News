from app.services.feedback.parser import parse_feedback_body, parse_feedback_commands


def test_parse_word_feedback() -> None:
    body = """LLDN_FEEDBACK
 token=abc
 type=word
 lesson_id=de-20260213
 language=de
 word=Schule
 status=fuzzy
"""
    cmd = parse_feedback_body(body, token="abc")
    assert cmd is not None
    assert cmd.command_type == "word"
    assert cmd.word == "Schule"
    assert cmd.word_status == "fuzzy"


def test_parse_grammar_feedback() -> None:
    body = """LLDN_FEEDBACK
 token=abc
 type=grammar
 lesson_id=de-20260213
 language=de
 topic=Verbzweitstellung
 mastered=true
"""
    cmd = parse_feedback_body(body, token="abc")
    assert cmd is not None
    assert cmd.command_type == "grammar"
    assert cmd.topic == "Verbzweitstellung"
    assert cmd.grammar_status == "mastered"


def test_parse_batch_feedback() -> None:
    body = """lln_feedback=1
 token=abc
 lesson_id=de-20260213
 language=de
 word_1_text=Schule
 word_1_status=unknown
 word_2_text=Stadt
 word_2_status=known
 grammar_topic=Verbzweitstellung
 grammar_status=review
"""
    cmds = parse_feedback_commands(body, token="abc")
    assert len(cmds) == 3
    assert any(c.command_type == "word" and c.word == "Schule" and c.word_status == "unknown" for c in cmds)
    assert any(c.command_type == "word" and c.word == "Stadt" and c.word_status == "known" for c in cmds)
    assert any(c.command_type == "grammar" and c.topic == "Verbzweitstellung" and c.grammar_status == "review" for c in cmds)


def test_parse_batch_feedback_ignores_token_mismatch() -> None:
    body = """lln_feedback=1
 token=abc
 lesson_id=de-20260213
 language=de
 word_1_text=Schule
 word_1_status=unknown
"""
    cmds = parse_feedback_commands(body, token="wrong")
    assert cmds == []
