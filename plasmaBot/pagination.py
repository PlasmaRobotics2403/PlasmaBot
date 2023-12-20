import discord
from discord.ext.commands import Context
from typing import Callable, Optional

from discord.interactions import Interaction

class Pagination(discord.ui.View):
    def __init__(self, author:discord.Member, ctx:Context, pages: Callable, *, timeout: int = 60):
        self.author = author
        self.ctx = ctx
        self.pages = pages
        self.total: Optional[int] = None
        self.index = 0
        self.message: Optional[discord.Message] = None;
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        else:
            embed = discord.Embed(
                description=f'Only the author of this command ({self.author.mention}) can perform this action.',
                color=discord.Color.purple()
            )
            embed.set_author(name='Error', icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        
    async def navigate(self):
        pages = self.pages(self.index)
        embed, self.total = pages
        
        if self.total == 1:
            self.message = await self.ctx.send(embed=embed, ephemeral=True)
        else:
            self.update_buttons()
            self.message = await self.ctx.send(embed=embed, view=self, ephemeral=True)

    async def edit_page(self, interaction: discord.Interaction):
        embed, self.total = self.pages(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def update_buttons(self):
        if self.index > (self.total // 2):
            self.children[2].emoji = '⏮️'
        else:
            self.children[2].emoji = '⏭️'
        self.children[0].disabled = self.index == 0
        self.children[1].disabled = self.index == (self.total - 1)
    
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