import requests
import time

bot_token = '5196468787:AAEp6uQwtCf0EowU6Fuz5UeK2Xh1ua8HV1U'  # токен из бота @BotFather
chat_id = '320033881'  # id из бота @getmyid_bot

telegram_delay = 8


def getTPSLfrom_telegram():
    strr = 'https://api.telegram.org/bot' + bot_token + '/getUpdates'
    response = requests.get(strr)
    rs = response.json()
    rs2 = rs['result'][-1]
    rs3 = rs2['message']
    textt = rs3['text']
    datet = rs3['date']

    if (time.time() - datet) < telegram_delay:
        if 'quit' in textt:
            quit()
        if 'exit' in textt:
            exit()
        if 'hello' in textt:
            telegram_bot_sendtext('Hello. How are you?')


def telegram_bot_sendtext(bot_message):
    bot_token2 = bot_token
    bot_chatID = chat_id
    send_text = 'https://api.telegram.org/bot' + bot_token2 + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()


starttime = time.time()
timeout = time.time() + 60 * 60 * 12  # 60 seconds times 60 meaning the script will run for 1 hr
counterr = 1

while time.time() <= timeout:
    try:
        print("passthrough at " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        getTPSLfrom_telegram()
        time.sleep(10 - ((time.time() - starttime) % 10.0))  # 1 minute interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()
