import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed, create_error_embed
from ..utils.tenant import tenant_db
import sqlite3
import json
import os
import io

class QAAnswerModal(discord.ui.Modal):
    def __init__(self, question_data):
        super().__init__(title=f"回答問題: {question_data['title'][:30]}...")
        self.question_data = question_data

        self.answer = discord.ui.TextInput(
            label="您的答案",
            placeholder="請輸入您的答案",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )

        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        user_answer = self.answer.value.strip().lower()

        # Check answers (case-insensitive, whitespace ignored)
        correct_answers = [ans.strip().lower() for ans in self.question_data['answers']]
        is_correct = any(user_answer == correct_ans for correct_ans in correct_answers)

        if is_correct:
            # Add points
            points = self.question_data['points']
            with sqlite3.connect("data/tenant.db") as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO scores (guild_id, user_id, score) VALUES (?, ?, 0)
                """, (guild_id, user_id))
                conn.execute("""
                    UPDATE scores SET score = score + ? WHERE guild_id = ? AND user_id = ?
                """, (points, guild_id, user_id))

                # Get new total score
                cursor = conn.execute(
                    "SELECT score FROM scores WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id)
                )
                new_score = cursor.fetchone()[0]

            embed = create_success_embed(
                title="🎉 答對了！",
                description=f"**獲得分數：** +{points}\n**總分數：** {new_score}",
                guild_name=interaction.guild.name
            )

            # Try CTFd sync if available
            try:
                await self.sync_ctfd_award(interaction, points)
            except:
                pass  # Ignore CTFd sync errors

        else:
            embed = create_error_embed(
                title="❌ 答錯了",
                description=f"正確答案：{' / '.join(self.question_data['answers'])}",
                guild_name=interaction.guild.name
            )

        # Handle long content
        if len(embed.description) > 2000:
            # Create file attachment
            file_content = f"題目: {self.question_data['title']}\n"
            file_content += f"您的答案: {self.answer.value}\n"
            file_content += f"結果: {'正確' if is_correct else '錯誤'}\n"
            if not is_correct:
                file_content += f"正確答案: {' / '.join(self.question_data['answers'])}\n"
            if is_correct:
                file_content += f"獲得分數: +{points}\n總分數: {new_score}\n"

            file = discord.File(io.StringIO(file_content), filename="qa_result.txt")
            embed.description = "回答結果詳情請見附件。"
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def sync_ctfd_award(self, interaction: discord.Interaction, points: int):
        """Try to sync award to CTFd"""
        try:
            ctfd_cog = interaction.client.get_cog('CTFdCog')
            if ctfd_cog:
                await ctfd_cog.award_ctfd_points(
                    interaction.guild.id,
                    interaction.user.id,
                    points
                )
        except:
            pass  # Ignore CTFd sync errors

class QACog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qa_bank_file = "data/qa_bank.json"
        self.ensure_qa_bank_exists()

    def ensure_qa_bank_exists(self):
        """Ensure QA bank file exists"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.qa_bank_file):
            with open(self.qa_bank_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def load_qa_bank(self):
        """Load QA bank from file"""
        try:
            with open(self.qa_bank_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_qa_bank(self, questions):
        """Save QA bank to file"""
        with open(self.qa_bank_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

    def get_next_question_id(self, questions):
        """Get next available question ID"""
        if not questions:
            return 1
        return max(q.get('id', 0) for q in questions) + 1

    @app_commands.command(name="qa_add", description="新增題目")
    @app_commands.describe(
        title="題目標題",
        answer="答案（用 ; 分隔多個答案）",
        points="分數"
    )
    async def qa_add(
        self,
        interaction: discord.Interaction,
        title: str,
        answer: str,
        points: int
    ):
        # Check permission
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有管理員可以新增題目。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Parse answers
        answers = [ans.strip() for ans in answer.split(';') if ans.strip()]

        if not answers:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 答案格式錯誤",
                    description="請提供至少一個答案。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Load and update QA bank
        questions = self.load_qa_bank()
        question_id = self.get_next_question_id(questions)

        new_question = {
            "id": question_id,
            "title": title,
            "answers": answers,
            "points": points
        }

        questions.append(new_question)
        self.save_qa_bank(questions)

        embed = create_success_embed(
            title="✅ 題目已新增",
            description=f"**ID：** {question_id}\n**標題：** {title}\n**分數：** {points}",
            guild_name=interaction.guild.name
        )
        embed.add_field(name="答案", value=" / ".join(answers), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="qa_ask", description="出題")
    @app_commands.describe(qid="題目ID")
    async def qa_ask(self, interaction: discord.Interaction, qid: int):
        questions = self.load_qa_bank()
        question = next((q for q in questions if q.get('id') == qid), None)

        if not question:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 題目不存在",
                    description=f"找不到ID為 {qid} 的題目。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Create question embed
        embed = create_brand_embed(
            title=f"📝 題目 #{qid}",
            description=question['title'],
            guild_name=interaction.guild.name
        )
        embed.add_field(name="分數", value=f"{question['points']} 分", inline=True)

        # Create modal for answer
        modal = QAAnswerModal(question)

        # Check if question is too long for embed
        if len(question['title']) > 2000:
            # Send as attachment
            file_content = f"題目 #{qid}\n\n{question['title']}\n\n分數: {question['points']} 分"
            file = discord.File(io.StringIO(file_content), filename=f"question_{qid}.txt")
            embed.description = "題目內容過長，請見附件。"
            await interaction.response.send_message(embed=embed, file=file)
            await interaction.followup.send("請點擊按鈕回答:", view=QAAnswerView(question), ephemeral=True)
        else:
            await interaction.response.send_modal(modal)

    @app_commands.command(name="qa_scoreboard", description="顯示排行榜")
    async def qa_scoreboard(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.execute("""
                SELECT user_id, score FROM scores
                WHERE guild_id = ? AND score > 0
                ORDER BY score DESC LIMIT 10
            """, (guild_id,))
            scores = cursor.fetchall()

        if not scores:
            embed = create_brand_embed(
                title="🏆 排行榜",
                description="目前還沒有分數記錄。",
                guild_name=interaction.guild.name
            )
        else:
            leaderboard = []
            for i, (user_id, score) in enumerate(scores, 1):
                user = interaction.guild.get_member(user_id)
                username = user.display_name if user else f"User {user_id}"

                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                leaderboard.append(f"{medal} **{username}** - {score} 分")

            embed = create_brand_embed(
                title="🏆 排行榜 (Top 10)",
                description="\n".join(leaderboard),
                guild_name=interaction.guild.name
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="qa_reset", description="重置所有分數")
    async def qa_reset(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有管理員可以重置分數。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        with sqlite3.connect("data/tenant.db") as conn:
            conn.execute("DELETE FROM scores WHERE guild_id = ?", (guild_id,))

        embed = create_success_embed(
            title="🗑️ 分數已重置",
            description="所有分數已清零。",
            guild_name=interaction.guild.name
        )

        await interaction.response.send_message(embed=embed)

class QAAnswerView(discord.ui.View):
    """View for handling QA answers when question is sent as file"""
    def __init__(self, question_data):
        super().__init__(timeout=300)
        self.question_data = question_data

    @discord.ui.button(label="回答問題", style=discord.ButtonStyle.primary, emoji="✍️")
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = QAAnswerModal(self.question_data)
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(QACog(bot))