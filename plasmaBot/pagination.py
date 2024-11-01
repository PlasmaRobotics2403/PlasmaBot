import discord
from discord.ext.commands import Context
from typing import Callable, Optional

class Pagination(discord.ui.View):
    def __init__(self, author:discord.Member, ctx:Context, pages: Callable, *, timeout: int = 60):
        self.author = author
        self.ctx = ctx
        self.pages = pages
        self.total: Optional[int] = None
        self.index = 0
        self.message: Optional[discord.Message] = None
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        else:
            await interaction.response.send_message(f'Only {self.author.mention} can use this button.', ephemeral=True)
            return False
        
    async def navigate(self):
        pages = await self.pages(self.index)
        embed, self.total = pages
        
        if self.total == 1:
            if self.ctx.interaction:
                self.message = await self.ctx.send(embed=embed, ephemeral=True)
            else:
                await self.ctx.message.reply(embed=embed)
        else:
            await self.update_buttons()
            if self.ctx.interaction:
                self.message = await self.ctx.send(embed=embed, view=self, ephemeral=True)
            else:
                self.message = await self.ctx.message.reply(embed=embed, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        embed, self.total = await self.pages(self.index)
        await self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def update_buttons(self):
        self.children[0].disabled = self.index == 0
        self.children[1].disabled = self.index == 0
        self.children[2].disabled = self.index == self.total//2
        self.children[3].disabled = self.index == (self.total - 1)
        self.children[4].disabled = self.index == (self.total - 1)
    
    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.gray)
    async def first(self, interaction: discord.Interaction, button: discord.Button):
        if self.index != 0:
            self.index = 0
            await self.edit_page(interaction)
        else:
            await interaction.response.send_message('You are already on the first page.', ephemeral=True)

    @discord.ui.button(emoji='⬅️', style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        if self.index > 0:
            self.index -= 1
            await self.edit_page(interaction)
        else:
            await interaction.response.send_message('You are already on the first page.', ephemeral=True)

    @discord.ui.button(emoji='↕️', style=discord.ButtonStyle.gray)
    async def mid(self, interaction: discord.Interaction, button: discord.Button):
        if self.index != self.total//2:
            self.index = self.total//2
            await self.edit_page(interaction)
        else:
            await interaction.response.send_message('You are already on the middle page.', ephemeral=True)

    @discord.ui.button(emoji='➡️', style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        if self.index < (self.total - 1):
            self.index += 1
            await self.edit_page(interaction)
        else:
            await interaction.response.send_message('You are already on the last page.', ephemeral=True)

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.gray)
    async def last(self, interaction: discord.Interaction, button: discord.Button):
        if self.index != self.total-1:
            self.index = self.total-1
            await self.edit_page(interaction)
        else:
            await interaction.response.send_message('You are already on the last page.', ephemeral=True)

    async def on_timeout(self):
        await self.message.edit(view=None)