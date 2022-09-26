import interactions as di
from functions_sql import SQL
import config as c
from datetime import datetime
from typing import Type
import sched, time
import asyncio

class Schedule(di.Extension):
    def __init__(self, client) -> None:
        self.client = client
        self._SQL = SQL(database=c.database)
        self._schedule = sched.scheduler(time.time, time.sleep)

    @di.extension_listener
    async def on_start(self):
        self.channel = await di.get(client=self.client, obj=di.Channel, object_id=c.channel_sched)
        self._sched_activ = {}
        sched_list = self._SQL.execute(stmt="SELECT * FROM sched_list").data_all
        for s in sched_list:
            await self.add_schedule(id=s[0], title=s[1], timestamp=s[2], run=False)
        self._schedule.run()

    async def add_schedule(self, id: int, title: str, timestamp: str, run:bool = True):
        t = datetime.strptime(timestamp, "%d.%m.%Y %H:%M")
        roles = self._SQL.execute(stmt="SELECT ment_id FROM sched_mentions WHERE ment_type='role' AND id=?", var=(id,)).data_all
        users = self._SQL.execute(stmt="SELECT ment_id FROM sched_mentions WHERE ment_type='user' AND id=?", var=(id,)).data_all
        sched_id = self._schedule.enterabs(t.timestamp(), 1, self._exec, kwargs={'id':id, 'title':title, 'roles':roles, 'users': users})
        self._sched_activ[id] = (sched_id, t)
        if run: self._schedule.run()

    def _exec(self, **kwargs):
        asyncio.create_task(self._execute(kwargs=kwargs))

    async def _execute(self, **kwargs):
        title: str = kwargs.pop("title", None)
        roles: list[di.Role] = kwargs.pop("roles", None)

        users: list[di.User] = kwargs.pop("users", None)
        text = f"{' '.join([f'<@{u}>' for u in users]) if users else ''}\n{' '.join([f'<@&{r}>' for r in roles]) if roles else ''}"
        text += f"\n\n{title}"
        await self.channel.send(text)
        id: int = kwargs.pop("id", None)
        print(self._schedule.queue)
        self._sql_del_schedule(id=id)
        print(self._sched_activ)
        self._sched_activ.__delitem__(id)
        print(self._sched_activ)

    def _sql_del_schedule(self, id: int):
        stmt = "DELETE FROM sched_list WHERE id=?"
        self._SQL.execute(stmt=stmt, var=(id,))
        stmt = "DELETE FROM sched_mentions WHERE id=?"
        self._SQL.execute(stmt=stmt, var=(id,))
    
    def _sql_add_schedule(self, title: str, time: str, **kwargs):
        stmt = "INSERT INTO sched_list(title, time) VALUES (?, ?)"
        insert_id = self._SQL.execute(stmt=stmt, var=(title, time,)).lastrowid
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
    @di.option()
    @di.option()
    @di.option()
    @di.option()
    async def add_reminder(self, ctx: di.CommandContext, title: str, time: str, mention_role: di.Role = None, mention_user: di.User = None):
        id = self._sql_add_schedule(title=title, time=time, ment_role=mention_role, ment_user=mention_user)
        await self.add_schedule(id=id, title=title, timestamp=time, run=True)
        await ctx.send(f"set Timer ```{title}``` at {time}")




def setup(client):
    Schedule(client)
