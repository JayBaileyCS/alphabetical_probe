from evals.spelling_by_grade import *

# Evals
FULL_SPELLING_EVAL = GradeSpellingEval("Spell Full Word", 
                                       create_full_spelling_prompt, 
                                       format_full_spelling_response, 
                                       get_spelling_accuracy)
GET_FIRST_LETTER_EVAL = GradeSpellingEval("Spell First Letter", 
                                          create_first_letter_spelling_prompt, 
                                          format_first_letter_response, 
                                          get_spelling_accuracy)
GET_POSITION_OF_LETTER_EVAL = GradeSpellingEval("Get Position of Letter In Word", 
                                                create_position_of_letter_spelling_prompt, 
                                                format_position_of_letter_response, 
                                                get_position_of_letter_accuracy)

EVAL_LIST = [FULL_SPELLING_EVAL, GET_FIRST_LETTER_EVAL, GET_POSITION_OF_LETTER_EVAL]