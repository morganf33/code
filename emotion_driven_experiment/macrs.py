import os
import openai
import csv
import json
import time
from time import sleep
import re

import user_simulator_w_emotion

def long_contact_dialogue(dialogue):
    dialogue_str = ""
    for r in dialogue:
        if r[0] == 'User':
            dialogue_str += r[0] + ': ' + r[1] + '\n'
        else:
            dialogue_str += 'Assistant: ' + r[1] + '\n'

    return dialogue_str

def short_contact_dialogue(dialogue):
    dialogue_str = ""
    if len(dialogue) <= 3:
        for r in dialogue:
            if r[0] == 'User':
                dialogue_str += r[0] + ': ' + r[1] + '\n'
            else:
                dialogue_str += 'Assistant: ' + r[1] + '\n'
    else:
        if dialogue[-3][0] == 'User':
            for r in dialogue[-3:]:
                if r[0] == 'User':
                    dialogue_str += r[0] + ': ' + r[1] + '\n'
                else:
                    dialogue_str += 'Assistant: ' + r[1] + '\n'
        else:
            for r in dialogue[-2:]:
                try:
                    if r[0] == 'User':
                        dialogue_str += r[0] + ': ' + r[1] + '\n'
                    else:
                        dialogue_str += 'Assistant: ' + r[1] + '\n'
                except BaseException:
                    exit(1)
    return dialogue_str

def check_result(response, target):
    target = target.split('(')[0].strip()
    if ',' in target:
        target = target.split(',')[0].strip()
    if target in response:
        return "yes"
    else:
        return "no"

def parse_suggest(input_string):
    pattern = r'\[(.*?)\]([^\[]*)'
    matches = re.findall(pattern, input_string)
    return [list(match) for match in matches]

def extract_placeholders(s):
    placeholders = []
    pattern = r'\[(.*?)\]'
    matches = re.findall(pattern, s)
    for match in matches:
        placeholders.append(match)
    return placeholders

def process_system_output(output):
    if '{response}:' in output:
        act = output.split('{response}:')[0].strip()
        act = act.replace('{dialogue act}:', '').strip()
        response = output.split('{response}:')[1].strip()
        return act, response
    else:
        return '', ''


class macrs:
    def __init__(self):
        openai.api_key = "your_api"

        self.recommender_prompt = """You are a helpful recommender. You should recommend a movie to the user and generate an engaging description of the movie.
And you have access to the user preferences, which include the user's requirements and past interaction between the user and you.
Occasionally, you may receive a suggestion that you can utilize to enhance your response.
Here is an example:
{user preference}:
User requirement: The user wants an animated romantic film. Past interaction: None.
{dialogue hisotry}:
User: I would like to find a romantic love movie against the backdrop of a disaster event.
{response}(No more than 25 words):
How about watching "Titanic"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship.

You MUST NOT give any explanation in your response. Now, please generate an output based on the below information.
"""

        self.question_prompt = """Your task is to obtain user requirements (such as genre, plot/theme, period/country, mood/tone, character).
You have access to your known user preferences and dialogue history between the user and you.
Occasionally, you may receive a suggestion that you can utilize to enhance your response.
Here is an example:
{user preference}:
The user wants an animated romantic film.
{dialogue history}:
User: Hi, I'm in the mood for a romantic film. Can you suggest something for me?
{response}(No more than 20 words):
Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?

You MUST NOT give any explanation in your response. Now, please generate an output based on the below information.
"""

        self.chat_prompt = """Your task is to chit-chat with the user to prevent him/her from feeling bored or shifting the dialogue topic.
You CANNOT recommend or suggest any movies (Very important!!!). For example, "What about <a movie>?" or "How about <a movie>?" is not allowed. Additionally, you cannot ask users any questions. 
Occasionally, you may receive a suggestion that you can utilize to enhance your response.
Here is an example:
{user preferences}:
The user wants an animated romantic film.
{dialogue history}:
User: I'm looking for a movie to watch that's a mix of romance and cartoon. Any suggestions?
Assistant: Sure. Which cartoon do you like best? Do you prefer something more relaxed or more serious? 
User: This day's work is really too tiring. I want to see some relaxing movies. I've seen "Zootopia" before. The love story between Judy and Nick is so interesting.
{response}(No more than 20 words):
Yes, I love "Zootopia" too. Disney is my favorite animation film studio.

You MUST NOT give any explanation in your response. Now, please generate an output based on the below information.
"""

        self.planner_prompt = "You are a helpful planner in a conversational recommender system. " \
                              "You are responsible for planning the dialogue flow and " \
                              "selecting the most appropriate dialogue act from [recommendation], [inquiry], and [casual conversation]. " \
                              "[Recommendation] refers to recommending items to the user. " \
                              "[Inquiry] refers to obtaining more user preferences. " \
                              "[Casual conversation] refers to preventing users from feeling bored or shifting the dialogue topic. " \
                              "\nYou have access to the [dialogue history] between you and the user. " \
                              "And you will be given three [candidate responses], as each of them corresponds to a different dialogue act. " \
                              "\nYou need to consider the following aspects: " \
                              "(1) The effectiveness of recommendations can be measured by factors such as the recommendation accuracy and the confidence in the recommended items. " \
                              "(2) The information gain; namely, how well the response can narrow down the range of recommendations. " \
                              "(3) The diversity of dialogue acts in the whole dialogue, because rigid and monotonous conversations are unwelcome. " \
                              "\nHere are some examples: " \
                              "\nExample 1" \
                              "\nInput:" \
                              "\n[dialogue history]: " \
                              "\nUser: I would like to find a romantic love movie against the backdrop of a disaster event." \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\n[Candidate response for inquiry]: What special elements do you like in a romantic love movie against the backdrop of a disaster event?" \
                              "\n[Candidate response for casual conversation]: I love romantic movies, too!" \
                              "\nOutput:" \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\nExample 2" \
                              "\nInput:" \
                              "\n[dialogue history]: " \
                              "\nUser: Hi, I'm in the mood for a romantic film. Can you suggest something for me?" \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\n[Candidate response for inquiry]: Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?" \
                              "\n[Candidate response for casual conversation]: I love romantic movies, too!" \
                              "\nOutput:" \
                              "\n[Candidate response for inquiry]: Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?" \
                              "\nExample 3" \
                              "\nInput:" \
                              "\n[dialogue history]: " \
                              "\nUser: Hi, I'm in the mood for a romantic film. Assistant: Sure. Which cartoon do you like best? Do you prefer something more relaxed or more serious? User: I've seen \"Zootopia\" before. The love story between Judy and Nick is so interesting." \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\n[Candidate response for inquiry]: Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?" \
                              "\n[Candidate response for casual conversation]: Yes, I love \"Zootopia\" too. Disney is my favorite animation film studio!" \
                              "\nOutput:" \
                              "\n[Candidate response for casual conversation]: Yes, I love \"Zootopia\" too. Disney is my favorite animation film studio!" \
                              "\nNow only output the response you choose and nothing else:"

        self.planner_prompt_with_ref = "You are a helpful planner in a conversational recommender system. " \
                              "You are responsible for planning the dialogue flow and " \
                              "selecting the most appropriate dialogue act from [recommendation], [inquiry], and [casual conversation]. " \
                              "[Recommendation] refers to recommending items to the user. " \
                              "[Inquiry] refers to obtaining more user preferences. " \
                              "[Casual conversation] refers to preventing users from feeling bored or shifting the dialogue topic. " \
                              "\nYou have access to the [dialogue history] between you and the user. " \
                              "And you will be given three [candidate responses], as each of them corresponds to a different dialogue act. " \
                              "\nYou need to consider the following aspects: " \
                              "(1) The effectiveness of recommendations can be measured by factors such as the recommendation accuracy and the confidence in the recommended items. " \
                              "(2) The information gain; namely, how well the response can narrow down the range of recommendations. " \
                              "(3) The diversity of dialogue acts in the whole dialogue, because rigid and monotonous conversations are unwelcome. " \
                              "\nHere are some examples: " \
                              "\nExample 1" \
                              "\nInput:" \
                              "\n[dialogue history]: " \
                              "\nUser: I would like to find a romantic love movie against the backdrop of a disaster event." \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\n[Candidate response for inquiry]: What special elements do you like in a romantic love movie against the backdrop of a disaster event?" \
                              "\n[Candidate response for casual conversation]: I love romantic movies, too!" \
                              "\nOutput:" \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\nExample 2" \
                              "\nInput:" \
                              "\n[dialogue history]: " \
                              "\nUser: Hi, I'm in the mood for a romantic film. Can you suggest something for me?" \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\n[Candidate response for inquiry]: Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?" \
                              "\n[Candidate response for casual conversation]: I love romantic movies, too!" \
                              "\nOutput:" \
                              "\n[Candidate response for inquiry]: Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?" \
                              "\nExample 3" \
                              "\nInput:" \
                              "\n[dialogue history]: " \
                              "\nUser: Hi, I'm in the mood for a romantic film. Assistant: Sure. Which cartoon do you like best? Do you prefer something more relaxed or more serious? User: I've seen \"Zootopia\" before. The love story between Judy and Nick is so interesting." \
                              "\n[Candidate response for recommendation]: How about watching \"Titanic\"? It is an epic romantic tragedy film that tells the story of love and loss aboard the ill-fated ship." \
                              "\n[Candidate response for inquiry]: Sure. Do you prefer romantic movies with a warm atmosphere or those with an emotional tone?" \
                              "\n[Candidate response for casual conversation]: Yes, I love \"Zootopia\" too. Disney is my favorite animation film studio!" \
                              "\nOutput:" \
                              "\n[Candidate response for casual conversation]: Yes, I love \"Zootopia\" too. Disney is my favorite animation film studio!" \
                              "You receive a suggestion: \"{past_reflection}\". And you need to draw upon this experience to make your current selection." \
                              "\nNow only output the response you choose and nothing else:"

        self.preference_reason_prompt = "According to the [dialogue history], please analyze the [user profile]. " \
                                        "You should put the factors that you think are more important in front " \
                                        "and ensure that no factor is overlooked!!!" \
                                        "\nThe output format should be: [User profile]: \"The user want ...\"" \
                                        "\n Just output the [user profile]. Don't explain. No more than 30 words!!!"

        self.interaction_reason_prompt = "Please analyze the user's attitude towards the movies mentioned in the [dialogue history]. " \
                                         "The relationships include \"have seen\", \"not interested and rejected the recommendation\", " \
                                         "and \"interested and accepted the recommendation\". " \
                                         "\nThe output format should be: " \
                                         "{\"MOVIE_NAME\": \"attitude\", \"MOVIE_NAME\": \"attitude\", ...}. " \
                                         "\nOnly movies mentioned in the conversation history should be included in the output. " \
                                         "If there are no movies mentioned in the conversation history, simply output \"None\" " \
                                         "\nThe [dialogue history] is: "

        self.high_reflect_prompt = """You are a good planner in the dialogue system. Your goal is to get as much user information as possible and provide accurate recommendations. 
In each round, you will receive user preference and output a system response. Then, the user will provide a user utterance as feedback.
The above information will form your action trajectory.
Based on your past action trajectory, your goal is to write a few sentences to explain why your recommendation failed as indicated by the user utterance. Only provide a few sentence description in your answer, which diagnoses a possible reason for failure and devise a concise plan that aims to mitigate the same failure.
Here are some examples:

{action trajectory}:
user preference 1: The user wants a movie in the action and thriller genre.
system response 1: What do you like about this action thriller movie?
user utterance 1: "The intense action scenes and dystopian setting in \"Blade Runner 2049\" caught my eye.
user preference 2: The user wants a dystopian setting with intense action scenes in the genre of action and thriller.
system response 2: How about "The Matrix"? It is a science fiction film exploring a dystopian future where reality is simulated by a computer system.
user utterance 2: I have seen "The Matrix". But I'm looking for a movie directed by Ron.
{reflection}:
In system response 1, I ask the user about the specific aspects. However, this conversation overlaps with our existing knowledge of the user's preference for action-thriller movies. I should choose to ask questions only when the questions can add more user information.
In system response 2, I recommend "The Matrix", and it meets part of user preferences. However, the user rejected the recommendation because the user is looking for movies directed by Ron. Next, I should recommend movies directed by Ron.

{action trajectory}:
user preference 1: The user wants an animated movie with a relaxing and romantic storyline from the production company Disney.
system response 1: How about "Zootopia"? This is a romantic comedy animated film produced by Disney.
user utterance 1: I have seen "Zootopia" and I love Disney. Can you suggest something else?
{reflection}:
In system response 1, I recommend "Zootopia", and it meets the user's preference. Since the user has already watched this movie, they rejected it. I should chit-chat with the user about Disney-related topics in order to uncover more of their preferences. 

Please think step by step. Now, please generate a system response based on the below information.
"""

        self.high_suggest_prompt = """You are a helpful assistant. You will be given a reflection. 
Based on reflection, you need to provide suggestions to different agents, which include "Planning Agent", "Recommending Agent", "Asking Agent" and "Chit-chatting Agent". Different agents are responsible for different tasks.
"Asking Agent" and "Chit-chatting Agent" are responsible for eliciting user preferences. "Recommending Agent" is responsible for providing recommendations based on user preferences. And "Planning Agent" is responsible for choosing the suitable dialogue action among "recommend", "ask" and "chit-chatting".
You need to generate several suggestions for "Recommending Agent", "Asking Agent" and "Chit-chatting Agent". Then you should report the suggestions to the "Planning Agent" as experience.
Here are some examples:

{reflection}:
In system response 1, I recommend "Zootopia". However, the user rejects the recommendation because of the storyline. Next, I should ask about the user preferences regarding the storyline.
{suggestion}:
[To Asking Agent] You should ask about the user preferences regarding the storyline.
{experience}:
[To Planning Agent] I suggest asking about the user preferences regarding the storyline.

{reflection}:
In system response 1, I ask the user about the specific aspects. However, this conversation overlaps with our existing knowledge of the user's preference for action-thriller movies. I should choose to ask questions only when the questions can add more user information.
In system response 2, I recommend "The Matrix", and it meets part of user preferences. However, the user reject the recommendation because the user is looking for movies directed by Ron. Next, I should recommend movies directed by Ron.
{suggestion}:
[To Asking Agent] You should carefully consider whether the topic you ask will bring new user information.
[To Recommending Agent] You should recommend movies directed by Ron.
{experience}:
[To Planning Agent] I suggest focusing on information gain when asking and suggest recommending movies directed by Ron.

{reflection}:
In system response 1, I recommend "Zootopia", and it meets the user's preference. Since the user has already watched this movie, they rejected it. I should chit-chat with the user about Disney-related topics in order to uncover more of their preferences. 
{suggestion}:
[To Chit-chatting Agent] You should chit-chat with the user about Disney-related topics in order to uncover more of their preferences.
{experience}:
[To Planning Agent] I suggest chit-chatting with the user about Disney-related topics in order to uncover more of their preferences.

Please think step by step. Now, please generate a response based on the below information.
"""

        self.recommender_list_prompt = """You are a helpful assistant to provide recommendation. You must follow the instructions below. 
The recommendation list must contain 10 items that are consistent with user preference. Furthermore, the higher the position of an item in the list, the greater its likelihood of recommendation.
The format of the recommendation list is: no. title (year). 
Don’t mention anything other than the title of items in your recommendation list.
Here is a example:
{user preference}:
The user wants a recommendation for a horror movie from the 1970s that features epic space operas and powerful orchestral scores.
{dialogue history}:
User: I'm looking for a epic space opera movie to watch.
Assistant: [Asking act] Sure. Which epic space opera movie do you like best?
User: I really liked "Alien".
Assistant: [Recommending act] How about watching "Se7en"?
User: I haven't seen "Se7en". But I prefer epic space operas from the 70s. Can you recommend something else?
{Recommend List}:
1. "Star Wars: Episode IV - A New Hope" (1977)
2. "Close Encounters of the Third Kind" (1977)
3. "Star Wars: Episode V - The Empire Strikes Back" (1980)
4. "2001: A Space Odyssey" (1968)
5. "The Godfather" (1972)
6. "Jaws" (1975)
7. "Apocalypse Now" (1979)
8. "Star Trek: The Motion Picture" (1979)
9. "Superman" (1978)
10. "The Deer Hunter" (1978)
Please think step by step. And please ONLY output a {Recommend List}. You MUST NOT give any explanation in your response.
Now, please generate a output based on the below information.
"""

    def ask(
            self,
            prompt: str,
    ):
        dialog = []
        dialog.append({"role": "user", "content": prompt})
        while True:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=dialog,
                    stream=False,
                    timeout=360,
                    temperature=0
                )
            except BaseException as e:
                continue
            break

        return response['choices'][0]['message']['content']


    def infer(self, memory, dialogue, user_requirement, past_interaction):
        if len(memory['recommend']) == 0:
            recommender_prompt = self.recommender_prompt + "\n{user preference}:\n" + 'User\'s requirement: ' + user_requirement + \
                                 '. Past interaction: ' + past_interaction + "\n{dialogue history}:\n" + short_contact_dialogue(dialogue) + "\n{response}(No more than 25 words):"

        else:
            recommender_prompt = self.recommender_prompt + "\n{user preference}:\n" + 'User\'s requirement: ' + user_requirement + \
                                 '. Past interaction: ' + past_interaction + "\n{dialogue history}:\n" + short_contact_dialogue(dialogue) + "\n{suggestion}:" + memory['recommend'][0] + "\n{response}(No more than 25 words):"

        recommender_response = self.ask(recommender_prompt)

        if len(memory['question']) == 0:
            question_prompt = self.question_prompt + "\n{user preference}:\n" + user_requirement + "\n{dialogue history}:\n" + short_contact_dialogue(dialogue) + "\n{response}(No more than 20 words): "

        else:
            question_prompt = self.question_prompt + "\n{user preference}:\n" + user_requirement + "\n{dialogue history}:\n" + short_contact_dialogue(dialogue) + "\n{suggestion}:" + memory['question'][
                                     0] + "\n{response}(No more than 20 words): "
        question_response = self.ask(question_prompt)

        if len(memory['chit-chat']) == 0:
            chat_prompt = self.chat_prompt + "\n{user preference}:\n" + user_requirement + "\n{dialogue history}:\n" + short_contact_dialogue(dialogue) + "\n{response}(No more than 20 words): "

        else:
            chat_prompt = self.chat_prompt + "\n{user preference}:\n" + user_requirement + "\n{dialogue history}:\n" + short_contact_dialogue(dialogue) + "\n{suggestion}:" + memory['chit-chat'][
                                  0] + "\n{response}(No more than 20 words): "
        chat_response = self.ask(chat_prompt)

        if len(memory['plan']) > 0:
            planner_prompt = self.planner_prompt_with_ref + '[dialogue history]: ' + long_contact_dialogue(dialogue) + \
                             '\n[Candidate response for recommendation]: ' + recommender_response + \
                             '\n[Candidate response for inquiry]: ' + question_response + \
                             '\n[Candidate response for casual conversation]: ' + chat_response + \
                             '\n[suggestions]: ' + ';'.join(memory['plan']) + '\nOutput: '
        else:
            planner_prompt = self.planner_prompt + '[dialogue history]: ' + long_contact_dialogue(dialogue) + \
                             '\n[Candidate response for recommendation]: ' + recommender_response + \
                             '\n[Candidate response for inquiry]: ' + question_response + \
                             '\n[Candidate response for casual conversation]: ' + chat_response + \
                             '\nOutput: '

        planner_response = self.ask(planner_prompt)

        if '[Candidate response' in planner_response and ']:' in planner_response:
            system_response = planner_response.split(']:')[1].strip()
            choice = planner_response.split(']:')[0].strip()
        elif 'Candidate response' in planner_response and ':' in planner_response:
            system_response = planner_response.split(':')[1].strip()
            choice = planner_response.split(':')[0].strip()
        else:
            system_response = planner_response
            choice = 'chat'

        return recommender_response, question_response, chat_response, planner_response, system_response

    def reflect(self, action_trajectory):
        memory = {
            'question': [],
            'chit-chat': [],
            'recommend': [],
            'plan': []
        }

        high_reflect_prompt = self.high_reflect_prompt + '\n{action trajectory}:\n'
        for i in range(len(action_trajectory['system_response'])):
            high_reflect_prompt += 'user preference ' + str(i + 1) + ': ' + action_trajectory['user_preference'][
                i] + '\n'
            high_reflect_prompt += 'system response ' + str(i + 1) + ': ' + action_trajectory['system_response'][
                i] + '\n'
            high_reflect_prompt += 'user utterance ' + str(i + 1) + ': ' + action_trajectory['user_utterance'][i] + '\n'

        high_reflect_prompt += '{reflection}:\n'
        high_reflection = self.ask(high_reflect_prompt)

        high_suggest_prompt = self.high_suggest_prompt + '\n{reflection}: ' + high_reflection + '\n{suggestion}:'
        high_suggest = self.ask(high_suggest_prompt)

        suggestion_list = parse_suggest(high_suggest)
        for ss in suggestion_list:
            ss[1] = ss[1].replace('{experience}:\n', '')
            ss[1] = ss[1].strip()
            if 'Recommend' in ss[0]:
                memory['recommend'].append(ss[1])
            elif 'Ask' in ss[0]:
                memory['question'].append(ss[1])
            elif 'Chit' in ss[0]:
                memory['chit-chat'].append(ss[1])
            elif 'Plan' in ss[0]:
                memory['plan'].append(ss[1])
        return memory, high_reflection, high_suggest

def main(infer_data):
    new_data = {
        'id': infer_data['id'],
        'past history': infer_data['past history'],
        'target item': infer_data['target item'],
        'item_summary': infer_data['item_summary'],
        'trajectory': []
    }

    memory = {
            'question': [],
            'chit-chat': [],
            'recommend': [],
            'plan': []
        }
    action_trajectory = {'user_preference': [],
                         'system_response': [],
                         'user_utterance': []}

    user_response = infer_data['user_start']
    user_simulator.reset_status()

    dialogue = [['User', user_response]]
    emotion_list = [2]
    turn = 1
    action_list = []
    while True:
        mem_prompt = macrs.preference_reason_prompt + "[Dialogue history]: " + long_contact_dialogue(dialogue) + "[User profile]: "
        user_requirement = macrs.ask(mem_prompt)

        mem_prompt = macrs.interaction_reason_prompt + long_contact_dialogue(
            dialogue)
        past_interaction = macrs.ask(mem_prompt)

        action_trajectory['user_preference'].append(user_requirement)

        recommender_response, question_response, chat_response, planner_response, system_response = macrs.infer(memory, dialogue, user_requirement, past_interaction)

        tra = {
               'turn': turn,
               'user': user_response,
               'user_emotion': user_simulator.now_emotion,
               'user_requirement': user_requirement,
               'past_interaction': past_interaction,
               'recommender_response': recommender_response,
               'question_response': question_response,
               'chat_response': chat_response,
               "planner_response": planner_response
               }
        turn += 1

        dialogue.append(['Assistant', system_response])
        action_trajectory['system_response'].append(system_response)

        check_response = check_result(system_response, infer_data['target item'][0])

        if 'yes' in check_response:
            new_data['trajectory'].append(tra)
            new_data['end'] = 'success'
            return new_data

        if 'yes' in check_response:
            new_data['trajectory'].append(tra)
            new_data['end'] = 'success'
            return new_data

        try:
            user_response, action, rec_result, rec_item = user_simulator.generate_user_response(dialogue,
                                                                                                system_response,
                                                                                                '[' + '; '.join(
                                                                                                    infer_data[
                                                                                                        'past history']) + ']',
                                                                                                infer_data[
                                                                                                    'item_summary'],
                                                                                                infer_data[
                                                                                                    'target item'],
                                                                                                infer_data[
                                                                                                    'past history'],
                                                                                                action_list)
        except BaseException:
            new_data['end'] = 'not_end'
            break
        if user_response is None:
            new_data['end'] = 'not_end'
            break

        action_list.append(action)
        dialogue.append(["User", user_response])
        emotion_list.append(user_simulator.now_emotion)

        if len(emotion_list) >= 2 and sum(emotion_list[-2:]) == 0:
            new_data['trajectory'].append(tra)
            new_data['end'] = 'fail'

            mem_prompt = macrs.preference_reason_prompt + "[Dialogue history]: " + long_contact_dialogue(
                dialogue) + "[User profile]: "
            user_requirement = macrs.ask(mem_prompt)

            macrs_recommender_list_prompt = macrs.recommender_list_prompt + "\n{user preference}:\n" + user_requirement + "\n{dialogue history}:\n" + long_contact_dialogue(
                dialogue) + "\n{Recommend List}:"
            macrs_recommender_list_response = macrs.ask(macrs_recommender_list_prompt)

            tra = {
                'user': user_response,
                'user_requirement': user_requirement,
                'past_interaction': past_interaction,
            }
            new_data['recommender_list'] = macrs_recommender_list_response,
            new_data['trajectory'].append(tra)
            return new_data

        if turn > 5:
            new_data['trajectory'].append(tra)
            new_data['end'] = 'fail'

            mem_prompt = macrs.preference_reason_prompt + "[Dialogue history]: " + long_contact_dialogue(
                dialogue) + "[User profile]: "
            user_requirement = macrs.ask(mem_prompt)

            macrs_recommender_list_prompt = macrs.recommender_list_prompt + "\n{user preference}:\n" + user_requirement + "\n{dialogue history}:\n" + long_contact_dialogue(dialogue) + "\n{Recommend List}:"
            macrs_recommender_list_response = macrs.ask(macrs_recommender_list_prompt)

            tra = {
                'user': user_response,
                'user_requirement': user_requirement,
                'past_interaction': past_interaction,
            }
            new_data['recommender_list'] = macrs_recommender_list_response,
            new_data['trajectory'].append(tra)
            return new_data

        action_trajectory['user_utterance'].append(user_response)

        if 'rec' in action:
            memory, high_reflection, high_suggest = macrs.reflect(action_trajectory)
            action_trajectory = {'user_preference': [],
                                 'system_response': [],
                                 'user_utterance': []}
            tra['high_reflection'] = high_reflection
            tra['high_suggest'] = high_suggest
            tra['memory'] = memory
        else:
            memory = {
                'question': [],
                'chit-chat': [],
                'recommend': [],
                'plan': []
            }

        new_data['trajectory'].append(tra)

macrs = macrs()
user_simulator = user_simulator_w_emotion.user_simulator()
infer_dataset = json.load(open('/dataset/input_samples.json'))
infer_id_2_data = {}
for data in infer_dataset:
    infer_id_2_data[data['id']] = data

json_save_path = '/dataset/macrs_emotion.json'
new_dataset = json.load(open(json_save_path))
have_generated = []
for data in new_dataset:
    have_generated.append(data['id'])
for data in infer_dataset:
    if data['id'] in have_generated:
        continue
    new_data = main(data)
    if new_data is None:
        continue
    new_dataset.append(new_data)
    json.dump(new_dataset, open(json_save_path, 'w'), indent=4)