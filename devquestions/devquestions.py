from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
from datetime import datetime
import discord
import os


RED_SID = "240154543684321280"


def _in_red_server_check(ctx):
    return ctx.message.server.id == RED_SID


def check_in_red_server():
    return commands.check(_in_red_server_check)


class DevQuestions():
    """Module for asking questions as well as selecting
       questions to be answered"""

    def __init__(self, bot):
        self.bot = bot
        self.filepath = "data/devquestions/questions.json"
        self.questions = dataIO.load_json(self.filepath)
        self.priority_role = "Patron"
        # probably save a query as priority later instead of role /shrug

    @check_in_red_server()
    @commands.command(pass_context=True, name="askdev")
    async def askdev(self, ctx, question):
        """Submits a question to the queue"""
        question_timestamp = ctx.message.timestamp.timestamp()
        author = ctx.message.author
        # could also implement some sort of weighting algo that takes into
        # account user roles / # answered / q-a ratio / long-standing members
        # instead of making the user remember all the search params n such
        asker = self.questions["users"].setdefault(author.id, {"asked": 0,
                                                               "answered": 0})
        asker["asked"] += 1
        question = {
            "author": author.id,
            "question": question,
            "timestamp": question_timestamp
        }
        self.questions["list"].append(question)
        dataIO.save_json(self.filepath, self.questions)
        await self.bot.say("Question submitted to the queue")

    @check_in_red_server()
    @checks.admin_or_permissions(manage_server=True)
    @commands.command(pass_context=True, name="getquestion")
    async def get_question(self, ctx, role: discord.Role=None):
        """Command for getting a submitted question"""
        server = ctx.message.server
        try:
            role = role or [r for r in server.roles if r.name == self.priority_role][0]
        except:
            return await self.bot.say("I could not find the  role")

        # palm's code exhausts the "priority" role's questions first
        # this will stay true to that
        q_list = self.questions['list']
        try:
            question = next((q_list.remove(q) or q for q in q_list
                             if role in server.get_member(q["author"]).roles
                             ), q_list.pop(0))
            self.questions["users"][question["author"]]["answered"] += 1
            asker = server.get_member(question["author"])
            timestamp = datetime.fromtimestamp(question["timestamp"])
            await\
                self.bot.say("Question asked by {} at "
                             "{}: {}".format(asker.mention, timestamp,
                                             question["question"]))
            dataIO.save_json(self.filepath, self.questions)
        except IndexError:
            await self.bot.say("There are no more questions!")


def check_folder():
    if not os.path.exists("data/devquestions"):
        os.makedirs("data/devquestions")


def check_file():
    f = "data/devquestions/questions.json"
    data = {
        "users": {},
        "list": []
    }
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, data)


def setup(bot):
    check_folder()
    check_file()
    n = DevQuestions(bot)
    bot.add_cog(n)
