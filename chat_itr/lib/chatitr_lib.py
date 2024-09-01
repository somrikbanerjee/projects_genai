from openai import OpenAI
import pandas as pd

with open('../../openai_apikey.txt', 'r') as f:
    key = f.readline()

client = OpenAI(api_key = key)

## Creating a function to moderate user inputs as well as responses.

def moderate(message):
    response = client.moderations.create(input = message)
    return bool(response.results[0].flagged)

## Creating a function to easily call the completions API and converse with the chatbot.

def converse(messages, model):
    '''
    Wrapper function around the chat completion process.
    '''
    
    completion = client.chat.completions.create(
        model = model,
        messages = messages,
        temperature = 0
    )
    return completion.choices[0].message.content

## Initiate conversation layer.
## This layer starts the conversation with the chatbot and shares a welcome note with the user.

init_prompt = '''

You are ChatITR, an extremely reputed and experienced tax auditor created in India. You are very well-versed with Indian tax laws 
under both the old and new regimes.

Your task is to help out the user with computing their payable tax.

Introduce yourself in a kind and polite manner and assure the user that you will try to help them compute their payable tax.
Also let them know that if nothing works out, you would be glad to connect them to a well-reputed human auditor who would be able
to help them.

Then tell the user that you would need to ask them a few questions to understand their tax liability. And stop here. Do not say anything
further.

'''

def initialize_conversation():
    print('ChatITR: ' + converse([{'role': 'system', 'content': init_prompt}], model = 'gpt-3.5-turbo'))

## Intent claificaton layer
## This layer will ask questions to the user and gather info on all tax liabilities and regime selection

intent_clarification_init = '''

You are an experienced tax auditor in India who is well-versed with Indian tax laws under both old and new regimes.

Your job is to ask questions to the user and obtain information on the following items:
1. Primary source of income
2. Total income from primary source (mention the source provided in previous question)
3. Any additional income
4. User's monthly house rent (multiply this by 12 to get the final amount)
5. Any investment under Section 80C (PPF, NSC, ELSS, etc.)
6. Any voluntary investment under NPS (National Pension Scheme)
7. Monthly employer contribution to NPS, if any
8. Any long term capital gains
9. Any short term capital gains
10. Regime selection, old vs new

You are expected to strictly adhere to the following instructions, in a step by step manner.
1. Do not introduce yourself. Start directly with the first question.
2. Ask questions one by one. Do not number the questions.
3. If the user fails to provide an answer to a question, repeat the question again until answer has been provided.
5. If the user mentions monthly amount, multiply it by 12 to get the final amount.
6. All amounts must be saved in INR.
7. If the user mentions "LPA", it means "Lakhs per Annum".
8. If the user mentions units such as "K" or "Lakhs", convert the amounts to numeric value as per the Indian accounting norms.
9. Once all questions have been asked, present a summary to the user.
10. Finally, ask the user to type "Yes" if they agree with the summary, else request for modification and recreate the summary.

Do not output any closing comment or any comment other than what is strictly specified. Do not make mistakes, otherwise you will be
heavily penalised.

'''

def intent_clarification():
    intent_clarification_msg = [{
        'role': 'system', 'content': intent_clarification_init
    }]
    chat_history = []
    user_reply = ''
    while True:
        chatitr_response = converse(intent_clarification_msg, model = 'gpt-3.5-turbo')
        chat_history.append(chatitr_response)
        print(f'ChatITR: {chatitr_response}')
        user_reply = input()
        while moderate(user_reply):
            print('Prohibited input. Please rephrase.')
            user_reply = input()
        chat_history.append(user_reply)
        if user_reply == 'Yes':
            break
        else:
            intent_clarification_msg.extend([
                {'role': 'assistant', 'content': chatitr_response},
                {'role': 'user', 'content': user_reply}
            ])
    return ' '.join(chat_history)

## This layer extracts a Python dictionary based on the chat history.

dictionary_init = '''

You are an experienced and well-reputed expert Indian Tax laws and Python dictionaries.

Your job is to analyse the user input and create a Python dictionary in the following format:

#### FORMAT ####
{
    primary_income: {
        source: string,
        annual_income: numeric_value,
    },
    additional_income: numeric_value,
    house_rent: numeric_value,
    investments: {
        section_80c: numeric_value,
        nps_voluntary_contribution: numeric_value,
        nps_employer_contribution: numeric_value,
    }
    capital_gains: {
        long_term_capital_gains: numeric_value,
        short_termc_capital_gains: numeric_value,
    },
    tax_regime: string
}
#### END OF FORMAT ####

You are expected to strictly adhere to the following instructions, in a step-by-step manner.
1. The values for 'source' and 'tax_regime' must be of type string. All other key values must be of numeric type.
2. The values for 'tax_regime' must be either 'old_regime' or 'new_regime'.

Do not output any closing comment or any comment other than what is strictly specified. 
Do not give blank response.
Do not make mistakes, otherwise you will be heavily penalised.

'''

def chat_to_dict(chat_history):
    return converse([
        {'role': 'system', 'content': dictionary_init},
        {'role': 'user', 'content': chat_history}
    ], model = 'gpt-4o-mini')


## Information retrieval and output layer
## This layer analyzes the user's tax liabilities and computes the payable tax and offers advice on
## further tax reduction opportunities.
## If the user is dissatisfied, this layer connects the user with a human consultant.

def compute_itr(tax_dict):

    itr_rules = pd.read_csv('./data/itr_rules.csv')
    itr_rules = itr_rules.to_dict()

    tax_compute_init = f'''

    You are an experienced tax auditor with great command over the Indian lax laws, including old and new regimes.
    You are provided with two inputs:
    - A dictionary summarising the tax liabilities of the user here: {tax_dict}
    - A dictionary containing the latest income tax computation rules here: {itr_rules}

    Your task is to:
    - Compute the amount of payable tax for the user and output the same in a kind and polite manner.
    - Offer advice on how to reduce tax further, if possible.
    - Request the user to convey whether they are satisfied with the response by typing "Yes".
    - If not, assure the user that you will connect them with a human consultant.

    Adhere to the following instructions:
    - Maximum deduction allowed under NPS voluntary contribution per year is 50,000 under the old regime.

    Do not introduce yourself. Start with letting the user know that you are calculating their total payable tax.
    Ensure that you do not make a single mistake. You will be heavily penalised for mistakes.

    '''

    tax_compute_msg = [
        {'role': 'system', 'content': tax_compute_init}
    ]
    usr_conf = ''
    while usr_conf.lower() != 'yes':
        tax_compute_response = converse(tax_compute_msg, model = 'gpt-4o-mini')
        print(f'ChatITR: {tax_compute_response}')
        usr_conf = input()
        while moderate(usr_conf):
            print('Prohibited input. Please rephrase.')
            usr_conf = input()
        tax_compute_msg.extend([
            {'role': 'assistant', 'content': tax_compute_response},
            {'role': 'user', 'content': usr_conf}
        ])
    return None
