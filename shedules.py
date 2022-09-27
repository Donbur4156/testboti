import interactions as di
from functions_sql import SQL
import config as c
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Type
import sched, time
import asyncio

class Schedule(di.Extension):
    def __init__(self, client) -> None:
        self.client = client
        self._SQL = SQL(database=c.database)
        self._schedule = AsyncIOScheduler()

    @di.extension_listener
    async def on_start(self):
        self.channel = await di.get(client=self.client, obj=di.Channel, object_id=c.channel_sched)
        self._sched_activ = {}
        sched_list = self._SQL.execute(stmt="SELECT * FROM sched_list").data_all
        for s in sched_list:
            self.add_schedule(id=s[0], timestamp=s[2])
        self._schedule.start()

    def add_schedule(self, id: int, timestamp: str):
        t = datetime.strptime(timestamp, "%d.%m.%Y %H:%M")
        sched_id = self._schedule.add_job(self._execute, 'date', run_date=t, kwargs={'id': id})
        self._sched_activ[id] = {'job_id': sched_id.id, 'timestamp': timestamp}

    def change_schedule_time(self, id: int, timestamp: str):
        t = datetime.strptime(timestamp, "%d.%m.%Y %H:%M")
        job_id = self._sched_activ.get(id, {}).get('job_id')
        if not job_id: return False
        self._schedule.modify_job(job_id=job_id, next_run_time=t)
        self._sched_activ[id]['timestamp'] = timestamp


    async def _execute(self, id: int):
        roles = self._SQL.execute(stmt="SELECT ment_id FROM sched_mentions WHERE ment_type='role' AND id=?", var=(id,)).data_all
        users = self._SQL.execute(stmt="SELECT ment_id FROM sched_mentions WHERE ment_type='user' AND id=?", var=(id,)).data_all
        rem_text = self._SQL.execute(stmt="SELECT text FROM sched_list WHERE id=?", var=(id,)).data_single

        text = f"{' '.join([f'<@{u[0]}>' for u in users]) if users else ''}\n{' '.join([f'<@&{r[0]}>' for r in roles]) if roles else ''}"
        text += f"\n{rem_text[0]}"
        await self.channel.send(text)
        self._sql_del_schedule(id=id)
        self._sched_activ.__delitem__(id)

    def _sql_del_schedule(self, id: int):
        stmt = "DELETE FROM sched_list WHERE id=?"
        self._SQL.execute(stmt=stmt, var=(id,))
        stmt = "DELETE FROM sched_mentions WHERE id=?"
        self._SQL.execute(stmt=stmt, var=(id,))
    
    def _sql_add_schedule(self, text: str, time: str, **kwargs):
        stmt = "INSERT INTO sched_list(text, time) VALUES (?, ?)"
        insert_id = self._SQL.execute(stmt=stmt, var=(text, time,)).lastrowid
        ment_role: di.Role = kwargs.pop("ment_role", None)
        if ment_role: self._sql_add_mention_role(id=insert_id, role_id=int(ment_role.id))
        ment_user: di.User = kwargs.pop("ment_user", None)
        if ment_user: self._sql_add_mention_user(id=insert_id, user_id=int(ment_user.id))
        return insert_id

    def _sql_add_mention_role(self, id: int, role_id: int):
        stmt = "INSERT INTO sched_mentions(id, ment_type, ment_id) VALUES (?, ?, ?)"
        self._SQL.execute(stmt=stmt, var=(id, "role", role_id,))
        
    def _sql_add_mention_user(self, id: int, user_id: int):
        stmt = "INSERT INTO sched_mentions(id, ment_type, ment_id) VALUES (?, ?, ?)"
        self._SQL.execute(stmt=stmt, var=(id, "user", user_id,))


    @di.extension_command()
    async def reminder(self, ctx: di.CommandContext):
        pass

    @reminder.subcommand(name="add")
    @di.option(description="Benachrichtigungstext") #title
    @di.option(description="Zeitpunkt; Format: 'TT:MM:JJJJ hh:mm'") #time
    @di.option(description="Rolle, welche gepingt werden soll; weitere mit '/reminder add_role'") #mention_role
    @di.option(description="User, welche gepingt werden soll; weitere mit '/reminder add_user'") #mention_user
    async def reminder_add(self, ctx: di.CommandContext, base_res: di.BaseResult, text: str, time: str, mention_role: di.Role = None, mention_user: di.User = None):
        try:
            t = datetime.strptime(time, "%d.%m.%Y %H:%M")
        except ValueError:
            await ctx.send("Das angegebene Datum entspricht nicht dem Format `TT.MM.JJJJ HH:MM`", ephemeral=True)
            return False
        
        id = self._sql_add_schedule(text=text, time=time, ment_role=mention_role, ment_user=mention_user)
        self.add_schedule(id=id, timestamp=time)
        await ctx.send(f"set Timer at `{time}` (ID:{id})\n```{text}```")

    @reminder.subcommand(name="change_time")
    @di.option(description="ID des Reminders") #id
    @di.option(description="neuer Zeitpunkt; Format: 'TT:MM:JJJJ hh:mm'") #time
    async def reminder_changetime(self, ctx: di.CommandContext, base_res: di.BaseResult, id:int, time: str):
        try:
            t = datetime.strptime(time, "%d.%m.%Y %H:%M")
        except ValueError:
            await ctx.send("Das angegebene Datum entspricht nicht dem Format `TT.MM.JJJJ HH:MM`", ephemeral=True)
            return False
        self.change_schedule_time(id=id, timestamp=time)
        await ctx.send(f"new time for reminder id {id} was set: `{time}`")
        




def setup(client):
    Schedule(client)
