import asyncio
import random
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor

# здесь нужно указать токен вашего бота
API_TOKEN = ''

# инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# размеры поля
FIELD_WIDTH = 30
FIELD_HEIGHT = 4

# create engine and session
engine = create_engine('sqlite:///game.db')
Session = sessionmaker(bind=engine)
session = Session()

# create base class
Base = declarative_base()


# create user table
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    dino_x = Column(Integer)
    dino_y = Column(Integer)
    jumping = Column(Integer)
    seconds = Column(Integer)
    bad_cord = Column(Integer)
    bad_cord2 = Column(Integer)
    score = Column(Integer)


# обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # проверяем, есть ли пользователь в базе данных
    user_id = message.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        # если пользователь не найден, создаем новую запись в базе данных
        user = User(id=user_id, dino_x=0, dino_y=FIELD_HEIGHT - 1,
                    jumping=False, seconds=-1,
                    bad_cord=random.randint(10, 16),
                    bad_cord2=random.randint(19, 26), score=0)
        session.add(user)
        session.commit()
    dino_x = user.dino_x
    dino_y = user.dino_y
    jumping = user.jumping
    seconds = user.seconds
    bad_cords = user.bad_cord, user.bad_cord2
    score = user.score

    # отправляем сообщение с картой
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(
        types.InlineKeyboardButton(text='Jump', callback_data='jump'))
    map = ''
    for y in range(FIELD_HEIGHT):
        for x in range(FIELD_WIDTH):
            if x == dino_x and y == dino_y:
                map += '🦖'
            elif x in bad_cords and y == FIELD_HEIGHT - 1:
                map += '#'
            else:
                map += '. '
        map += '\n'
    sent_message = await message.answer(map, reply_markup=inline_keyboard)
    # запоминаем chat_id и message_id

    # запускаем функцию обновления сообщения
    await asyncio.sleep(1)
    asyncio.ensure_future(update_message(chat_id=sent_message.chat.id,
                                         message_id=sent_message.message_id))


# функция, которая будет отображать поле и динозаврика
async def update_message(chat_id, message_id):
    while True:
        # получаем данные пользователя из базы данных
        user_id = chat_id
        user = session.query(User).filter_by(id=user_id).first()
        dino_x = user.dino_x
        dino_y = user.dino_y
        jumping = user.jumping
        seconds = user.seconds
        bad_cords = user.bad_cord, user.bad_cord2
        score = user.score

        # создаем карту
        map = ''
        for y in range(FIELD_HEIGHT):
            for x in range(FIELD_WIDTH):
                if x == dino_x and y == dino_y:
                    map += '🦖'
                elif x in bad_cords and y == FIELD_HEIGHT - 1:
                    map += '#'
                else:
                    map += '. '
            map += '\n'
        try:
            # отправляем новое сообщение с картой
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_keyboard.add(
                types.InlineKeyboardButton(text='Jump', callback_data='jump'))
            await bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id, text=map,
                                        reply_markup=inline_keyboard)
        except exceptions.MessageNotModified:
            pass
        # перемещаем динозаврика
        if jumping and seconds > 0:
            jumping = False
        if jumping:
            # если кнопка "Jump" была нажата, перемещаем динозаврика вверх на 1 клетку
            dino_y -= 1
            # сбрасываем флаг прыжка
            jumping = False
            seconds = 4
        if seconds == 0:
            dino_y += 1
            seconds = -1
        elif seconds > 0:
            seconds -= 1
        if dino_y == FIELD_HEIGHT - 1 and dino_x in bad_cords:
            await bot.send_message(chat_id=chat_id, text='Game over')
            await bot.send_message(chat_id=chat_id,
                                   text=f"Your score: {dino_x + score}")
            # обновляем данные пользователя в базе данных
            user.dino_x = 0
            user.dino_y = FIELD_HEIGHT - 1
            user.jumping = False
            user.seconds = -1
            user.bad_cord = random.randint(10, 16)
            user.bad_cord2 = random.randint(19, 26)
            user.score = 0
            session.commit()
            return
        dino_x += 1
        if dino_x >= FIELD_WIDTH:
            score += dino_x
            dino_x = 0
            bad_cords = random.randint(6, 12), random.randint(16, 25)
        # обновляем данные пользователя в базе данных
        user.dino_x = dino_x
        user.dino_y = dino_y
        user.jumping = jumping
        user.seconds = seconds
        user.bad_cord = bad_cords[0]
        user.bad_cord2 = bad_cords[1]
        user.score = score
        session.commit()
        # ждем 1 секунду
        await asyncio.sleep(0.4)


# обработчик нажатия на кнопку "Jump"
@dp.callback_query_handler(text='jump')
async def jump_handler(message: types.Message):
    # получаем данные пользователя из базы данных
    user_id = message.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    # меняем флаг прыжка
    user.jumping = True
    session.commit()


# запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
