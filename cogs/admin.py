import discord
from discord.ext import commands
from discord.ext.commands import Cog
import traceback
import inspect
import re
import config
from helpers.checks import check_if_bot_manager
from helpers.userlogs import set_userlog


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_eval_result = None
        self.previous_eval_code = None

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command(name='exit', aliases=["quit", "bye", "stop", "kill", "restart", "die"])
    async def _exit(self, ctx):
        """Shuts down the bot, bot manager only."""
        await ctx.send(":wave: Goodbye!")
        await self.bot.logout()

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def fetchlog(self, ctx):
        """Returns log"""
        await ctx.send("Here's the current log file:",
                       file=discord.File(f"{self.bot.script_name}.log"))

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def fetchdata(self, ctx):
        """Returns data files"""
        data_files = [discord.File(fpath) for fpath in self.bot.wanted_jsons]
        await ctx.send("Here you go:", files=data_files)

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command(name='eval')
    async def _eval(self, ctx):
        await ctx.send("Fuck off. This doesn't belong in production code!")

    async def cog_load_actions(self, cog_name):
        if cog_name == "verification":
            verif_channel = self.bot.get_channel(config.welcome_channel)
            await self.bot.do_resetalgo(verif_channel, "cog load")

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def pull(self, ctx, auto=False):
        """Does a git pull, bot manager only."""
        tmp = await ctx.send('Pulling...')
        git_output = await self.bot.async_call_shell("git pull")
        await tmp.edit(content=f"Pull complete. Output: ```{git_output}```")
        if auto:
            cogs_to_reload = re.findall(r'cogs/([a-z_]*).py[ ]*\|', git_output)
            for cog in cogs_to_reload:
                try:
                    self.bot.unload_extension("cogs." + cog)
                    self.bot.load_extension("cogs." + cog)
                    self.bot.log.info(f'Reloaded ext {cog}')
                    await ctx.send(f':white_check_mark: `{cog}` '
                                   'successfully reloaded.')
                    await self.cog_load_actions(cog)
                except:
                    await ctx.send(f':x: Cog reloading failed, traceback: '
                                   f'```\n{traceback.format_exc()}\n```')
                    return

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def load(self, ctx, ext: str):
        """Loads a cog, bot manager only."""
        try:
            self.bot.load_extension("cogs." + ext)
            await self.cog_load_actions(ext)
        except:
            await ctx.send(f':x: Cog loading failed, traceback: '
                           f'```\n{traceback.format_exc()}\n```')
            return
        self.bot.log.info(f'Loaded ext {ext}')
        await ctx.send(f':white_check_mark: `{ext}` successfully loaded.')

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def unload(self, ctx, ext: str):
        """Unloads a cog, bot manager only."""
        self.bot.unload_extension("cogs." + ext)
        self.bot.log.info(f'Unloaded ext {ext}')
        await ctx.send(f':white_check_mark: `{ext}` successfully unloaded.')

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def reload(self, ctx, ext="_"):
        """Reloads a cog, bot manager only."""
        if ext == "_":
            ext = self.lastreload
        else:
            self.lastreload = ext

        try:
            self.bot.unload_extension("cogs." + ext)
            self.bot.load_extension("cogs." + ext)
            await self.cog_load_actions(ext)
        except:
            await ctx.send(f':x: Cog reloading failed, traceback: '
                           f'```\n{traceback.format_exc()}\n```')
            return
        self.bot.log.info(f'Reloaded ext {ext}')
        await ctx.send(f':white_check_mark: `{ext}` successfully reloaded.')

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def restoreuserlog(self, ctx, message_id: int):
        """Restores the user log from a saved backup."""
        message = await self.bot.botlog_channel.fetch_message(message_id)
        if message.author.id != self.bot.user.id or len(message.attachments) == 0:
            await ctx.send("Incorrect Message ID.")

        for attachment in message.attachments:
            if attachment.filename == "userlog.json":
                logs = (await attachment.read()).decode("utf-8")
                set_userlog(logs)
                return
        
        await ctx.send("Incorrect Message ID.")

def setup(bot):
    bot.add_cog(Admin(bot))
