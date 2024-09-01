import sys
sys.path.append(r'./lib')

from chatitr_lib import *

if __name__ == '__main__':
    initialize_conversation()
    chat_history = intent_clarification()
    tax_liab_dict = chat_to_dict(chat_history)
    compute_itr(tax_liab_dict)