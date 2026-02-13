from app.services.feedback.parser import parse_feedback_body


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
    assert cmd.mastered is True
