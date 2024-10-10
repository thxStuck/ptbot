import logging
import re
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import paramiko

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

FIND_EMAIL, FIND_PHONE, VERIFY_PASSWORD = range(3)

engine = create_engine('sqlite:///bot.db')
Base = declarative_base()

class Email(Base):
    __tablename__ = 'emails'
    id = Column(String, primary_key=True)
    email = Column(String)

class Phone(Base):
    __tablename__ = 'phones'
    id = Column(String, primary_key=True)
    phone = Column(String)

Base.metadata.create_all(engine)

def connect_to_server():
    ssh_host = os.getenv('SSH_HOST')
    ssh_port = int(os.getenv('SSH_PORT'))
    ssh_username = os.getenv('SSH_USERNAME')
    ssh_password = os.getenv('SSH_PASSWORD')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ssh_host, port=ssh_port, username=ssh_username, password=ssh_password)

    return ssh_client

def execute_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if error:
        return error
    else:
        return output

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Я бот для поиска информации. Используйте /find_email или /find_phone_number для поиска.')

async def find_email(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Пожалуйста, отправьте текст для поиска email-адресов.')
    return FIND_EMAIL

async def find_phone_number(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Пожалуйста, отправьте текст для поиска номеров телефонов.')
    return FIND_PHONE

async def verify_password(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Пожалуйста, отправьте пароль для проверки.')
    return VERIFY_PASSWORD

async def search_email(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        await update.message.reply_text(f'Найденные email-адреса: {", ".join(emails)}')
        # Сохранение email в БД
        session = sessionmaker(bind=engine)()
        for email in emails:
            email_db = Email(email=email)
            session.add(email_db)
        session.commit()
    else:
        await update.message.reply_text('Email-адреса не найдены.')
    return ConversationHandler.END

async def search_phone(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    phones = re.findall(r'\+?7[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}', text)
    if phones:
        await update.message.reply_text(f'Найденные номера телефонов: {", ".join(phones)}')
        # Сохранение номеров телефонов в БД
        session = sessionmaker(bind=engine)()
        for phone in phones:
            phone_db = Phone(phone=phone)
            session.add(phone_db)
        session.commit()
    else:
        await update.message.reply_text('Номера телефонов не найдены.')
    return ConversationHandler.END

async def check_password(update: Update, context: CallbackContext) -> int:
    password = update.message.text
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%* #?&]{8,}$'
    if re.match(pattern, password):
        await update.message.reply_text('Пароль сложный.')
    else:
        await update.message.reply_text('Пароль простой.')
    return ConversationHandler.END

async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Доступные команды:\n'
                                   '/start - начать работу с ботом\n'
                                   '/find_email - найти email-адреса\n'
                                   '/find_phone_number - найти номера телефонов\n'
                                   '/verify_password - проверить пароль\n'
                                   '/get_release - получить информацию о релизе\n'
                                   '/get_uname - получить информацию о системе\n'
                                   '/get_uptime - получить информацию о времени работы\n'
                                   '/get_df - получить информацию о файловой системе\n'
                                   '/get_free - получить информацию о свободной памяти\n'
                                   '/get_mpstat - получить информацию о производительности\n'
                                   '/get_w - получить информацию о работающих пользователях\n'
                                   '/get_auths - получить информацию о последних входах\n'
                                   '/get_critical - получить информацию о критических событиях\n'
                                   '/get_ps - получить информацию о запущенных процессах\n'
                                   '/get_ss - получить информацию о используемых портах\n'
                                   '/get_apt_list - получить информацию о установленных пакетах\n'
                                   '/get_services - получить информацию о запущенных сервисах\n'
                                   '/help - список доступных команд')

async def get_release(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'cat /etc/os-release')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_uname(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'uname -a')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_uptime(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'uptime')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_df(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'df -h')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_free(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'free -h')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_mpstat(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'mpstat -a')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_w(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'w')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_auths(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'last')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_critical(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'sudo journalctl -p crit')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_ps(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'ps aux')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_ss(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'ss -tunap')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_apt_list(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'apt list --installed')
    ssh_client.close()
    await update.message.reply_text(output)

async def get_services(update: Update, context: CallbackContext) -> None:
    ssh_client = connect_to_server()
    output = execute_command(ssh_client, 'systemctl list-units --type=service')
    ssh_client.close()
    await update.message.reply_text(output)

def main():
    TOKEN = os.getenv('TOKEN')
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), 
                      CommandHandler('find_email', find_email), 
                      CommandHandler('find_phone_number', find_phone_number), 
                      CommandHandler('verify_password', verify_password), 
                      CommandHandler('help', help),
                      CommandHandler('get_release', get_release),
                      CommandHandler('get_uname', get_uname),
                      CommandHandler('get_uptime', get_uptime),
                      CommandHandler('get_df', get_df),
                      CommandHandler('get_free', get_free),
                      CommandHandler('get_mpstat', get_mpstat),
                      CommandHandler('get_w', get_w),
                      CommandHandler('get_auths', get_auths),
                      CommandHandler('get_critical', get_critical),
                      CommandHandler('get_ps', get_ps),
                      CommandHandler('get_ss', get_ss),
                      CommandHandler('get_apt_list', get_apt_list),
                      CommandHandler('get_services', get_services)],
        states={
            FIND_EMAIL: [MessageHandler(filters.TEXT, search_email)],
            FIND_PHONE: [MessageHandler(filters.TEXT, search_phone)],
            VERIFY_PASSWORD: [MessageHandler(filters.TEXT, check_password)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
