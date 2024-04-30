import json
import time

import openai


class user_simulator:
    def __init__(self):
        openai.api_key = "your_api"

        self.user_simulator_prompt = "You are a user chatting with an assistant for movie recommendation in turn. " \
                                     "Your [requirements] for this time are: \"{target profile}\"."

        self.fail_rec_prompt = "The [dialogue history] between you and the assistant is: [{dialogue history}]. " \
                               "In the last turn of dialogue, the assistant recommended movie \"{recommend movie}\", which did not meet your [requirements]. " \
                               "Now, you need to identify the differences between the recommended movie and your [requirements], and select ONE of these features as a reason for rejecting. " \
                               "Then, you need to generate an emotional response based on your profile and the [dialogue history]. Your profile consists of [your emotion], your [requirements] and your [past preferences]. " \
                               "\nHowever, in your response, you should fuzzily indicate which aspect (e.g., genre, director/actors, time period/country, character, plot/theme, mood/tone, critical acclaim/award) of the recommended movie does not meet your [requirements], " \
                               "rather than specifically saying your [requirements]." \
                               "\nFor example, when one of your [requirements], such as 'fantasy setting', does not align with the recommended movie 'Titanic', " \
                               "you CAN NOT say \"I dislike 'Titanic' because it lacks a fantasy setting\". " \
                               "You CAN say \"I dislike 'Titanic' because its setting does not meet my requirement\"."

        self.have_seen_prompt = "The [dialogue history] between you and the assistant is: [{dialogue history}]. " \
                        "Now, you need to generate an emotional response based on your profile and the [dialogue history]. Your profile consists of your [emotion], your [requirements] and your [past preferences]. " \
                        "In the last turn of dialogue, the assistant recommended movie \"{recommend movie}\", which you have seen before. " \
                        "In your response, you need to inform the assistant about this and specify the features of the recommended movie that intrigued you before, based on your [past preferences]."

        self.accept_rec_prompt = "The [dialogue history] between you and the assistant is: [{dialogue history}]. " \
                                 "Now, you need to generate an emotional response based on your profile and the [dialogue history]. Your profile consists of your [emotion], your [requirements] and your [past preferences]. " \
                                 "In the last turn of dialogue, the assistant recommended movie \"{recommend movie}\", which meet your [requirements]. " \
                                 "In your response, you should present new aspects of your requirements rather than repeating information from the [dialogue history]."

        self.answer_question_prompt = "The [dialogue history] between you and the assistant is: [{dialogue history}]. In the last turn of dialogue, the assistant ask you a question: \"{last turn}\". "  \
                                      "You need to answer the question based on the [dialogue history] and your profile. Your profile consists of your [emotion], your [requirements] and your [past preferences]. " \
                                      "You can't repeat information from the [dialogue history]!!!" \


        self.chit_chat_prompt = "The [dialogue history] between you and the assistant is: [{dialogue history}]. In the last turn of dialogue, the assistant chit-chat with you and said \"{last turn}\". " \
                                "Based on your [requirements] and [past preferences], if your are interested in the topic mentioned in the last turn, you can choose to expand the topic. Otherwise, you can also change the topic according to your [requirements] and [past preferences]."

        self.emotion_prompt = "And you must determine the content and tone of your responses based on your [emotion]. " \
                              "For instance, when you are in low spirits, you may respond in a perfunctory manner or even refuse to answer the assistant. " \
                              "Conversely, you may disclose more your information when you're in a good mood." \
                              "Now, your [emotion] is \"{user emotion}\" "


        self.ps_prompt = "You can only provide a maximum of 2 features (such as the genre of the movie) in each response!!! " \
                         "Your response is only allowed to be the words from the user you act. Please remember you are just an ordinary user, try to use SIMPLE words!!" \
                         "Now act as a user and generate an emotional response that cannot exceed 20 words (very important!!!)."

        self.start_prompt = "Providing ONLY 1-2 features (such as the genre of the movie) in each response!!! " \
                            "Your response is only allowed to be the words from the user you act. Please remember you are just an ordinary user, try to use SIMPLE words!! " \
                            "And your response cannot exceed 20 words (very important!!!). Now lets start, you first, act as a user!!"

        self.emotion_list = ["Because of the inefficiency of the assistant, I am feeling dispirited and unwilling to provide ANY detailed information.",
                             "Because of the inefficiency of the assistant, I am feeling impatient.",
                             "I am relaxed and can chat with the assistant normally.",
                             "Because of the efficiency of the assistant, I am feeling satisfied.",
                             "Because of the efficiency of the assistant, I am feeling enthusiastic and willing to provide my detailed preferences."]
        self.now_emotion = 2

        self.classify_prompt = "Please determine the type of action that the sentence is performing: Recommendation, Inquiry, or Casual conversation. " \
                               "If the sentence contains a movie recommendation, it indicates \"Recommendation\". " \
                               "If the sentence involves eliciting user preferences, then it indicates \"Inquiry\". " \
                               "For other situations, it belongs to \"Casual conversation\"." \
                               "\nHere are some examples:" \
                               "\n{Sentence}: How about \"Saving Private Ryan\"? It's a war film set in the 70's. " \
                               "{Type}: Recommendation" \
                               "\n{Sentence}: Yes. It is an interesting movie. I love it, too! " \
                               "{Type}: Inquiry" \
                               "\n{Sentence}: Do you like drama movie? " \
                               "{Type}: Casual conversation"

        self.recommend_extract_prompt = "Please output which movie is recommend in the following sentence? " \
                                        "Just outpout the name of the movie!"
        self.fail_rec = 0

    def start_user(self, user_profile, target_profile):
        self.now_emotion = 2
        self.fail_rec = 0
        temp_prompt = self.user_simulator_prompt + "\n" + self.start_prompt
        temp_prompt = temp_prompt.replace("{user emotion}", self.emotion_list[self.now_emotion])
        temp_prompt = temp_prompt.replace("{user profile}", user_profile)
        temp_prompt = temp_prompt.replace("{target profile}", target_profile)
        start_response = self.ask(temp_prompt, temperature=0.2)
        return start_response

    def reset_status(self):
        self.now_emotion = 2
        self.fail_rec = 0

    def generate_user_response(self, dialogue_list, response, user_profile, target_profile, target_list, browsing_history, action_list,
                               action=None):
        if action == None:
            classify_prompt = self.classify_prompt + "\n{Sentence}: " + response + "{Type}: "
            raw_action = self.ask(classify_prompt, temperature=0)
            if "Recommendation" in raw_action:
                action = 'rec'
            elif "Inquiry" in raw_action:
                action = 'ask'
            else:
                action = 'chat'
        emotion = 0
        rec_result = None
        rec_item = None
        if action == 'rec':
            target_flag, rec_item = predict_match(target_list, response)
            have_seen_flag, _ = predict_match(browsing_history, response)
            if target_flag:
                result_prompt = self.accept_rec_prompt
                emotion = 1
                self.fail_rec = 0
                rec_result = 'accept'
            elif have_seen_flag:
                result_prompt = self.have_seen_prompt
                self.fail_rec = 0
                rec_result = 'have seen'
            else:
                result_prompt = self.fail_rec_prompt
                if self.fail_rec >= 1:
                    emotion = -1
                self.fail_rec += 1
                rec_result = 'reject'
            result_prompt = result_prompt.replace("{dialogue history}", contact_dialogue(dialogue_list))
        elif action == 'ask':
            self.fail_rec = 0
            result_prompt = self.answer_question_prompt
            result_prompt = result_prompt.replace("{dialogue history}", contact_dialogue(dialogue_list, -1))
            result_prompt = result_prompt.replace("{last turn}", dialogue_list[-1][1])
        else:
            self.fail_rec = 0
            result_prompt = self.chit_chat_prompt
            result_prompt = result_prompt.replace("{dialogue history}", contact_dialogue(dialogue_list, -1))

        if len(action_list) >= 2 and action == action_list[-1] and action == action_list[-2]:
            if emotion == 0:
                emotion = -1
                print('wrong action: ', '"'+action+'"', '"'+action_list[-1]+'"', '"'+action_list[-2]+'"')
        elif len(action_list) >= 2 and action != action_list[-1] and action != action_list[-2]:
            if emotion == 0:
                emotion = 1
                print('right action: ', '"'+action+'"', '"'+action_list[-1]+'"', '"'+action_list[-2]+'"')

        if emotion == 1:
            if self.now_emotion < 4:
                self.now_emotion += 1
        elif emotion == -1:
            if self.now_emotion > 0:
                self.now_emotion -= 1

        temp_prompt = self.user_simulator_prompt + "\n" + self.emotion_prompt + "\n" + result_prompt + "\n" + self.ps_prompt
        temp_prompt = temp_prompt.replace("{user profile}", user_profile)
        temp_prompt = temp_prompt.replace("{user emotion}", self.emotion_list[self.now_emotion])
        temp_prompt = temp_prompt.replace("{target profile}", target_profile)

        if action == 'rec':
            recommend_result = self.ask(self.recommend_extract_prompt + "\"" + response + "\"", temperature=0)
            if recommend_result[0] == '\"' or recommend_result[0] == '\'':
                recommend_result = recommend_result[1:]
            if recommend_result[-1] == '\"' or recommend_result[-1] == '\'':
                recommend_result = recommend_result[:-1]

            print('recommend_result', recommend_result)
            temp_prompt = temp_prompt.replace("{recommend movie}", recommend_result)

        wrong_times = 0
        while True:
            if wrong_times > 3:
                return None

            response = self.ask(temp_prompt, temperature=0.5)
            if 'User:' in response:
                response = response.split('User:')[1].strip()
            elif 'Assistant:' in response and 'User:' not in response:
                print('wrong response', response)
                time.sleep(10)

                wrong_times += 1
                continue
            if response == self.emotion_list[self.now_emotion] or self.emotion_list[self.now_emotion] in response:
                print('wrong response', response)
                time.sleep(10)

                wrong_times += 1
                continue
            if '\"' == response[0]:
                response = response[1:]
            if '\"' == response[-1]:
                response = response[:-1]
            return response, action, rec_result, rec_item

    def ask(
            self,
            prompt: str,
            temperature: float,
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
                    temperature=temperature
                )
            except BaseException as e:
                continue
            response = response['choices'][0]['message']['content']
            if len(response.split(' ')) >= 25:
                print('wrong response', response)
                return None
            break
        return response


def contact_dialogue(dialogue_list, end_pos=None):
    dialogue_str = ""
    start = 0
    if end_pos is None:
        for d in dialogue_list[start:]:
            if d[0] == 'User':
                dialogue_str += "You" + ": \"" + d[1] + "\" "
            else:
                dialogue_str += d[0] + ": \"" + d[1] + "\" "
        dialogue_str = dialogue_str[:-1]
    else:
        for d in dialogue_list[start:end_pos]:
            if d[0] == 'User':
                dialogue_str += "You" + ": \"" + d[1] + "\" "
            else:
                dialogue_str += d[0] + ": \"" + d[1] + "\" "
        dialogue_str = dialogue_str[:-1]
    return dialogue_str


def predict_match(info_list, recommend_response):
    for i in info_list:
        temp = i.split('(')[0].strip()
        if ',' in temp:
            if 'The' in temp.split(',')[1]:
                temp = 'The ' + temp.split(',')[0]
                temp = temp.strip()
            else:
                temp = temp.split(',')[0].strip()
        if temp in recommend_response:
            return True, i
    return False, None