# -*- coding: utf-8 -*-
def create_auto_activate_middleware(toolkit):
    async def middleware(kwargs: dict, next_handler):
        tool_call = kwargs.get("tool_call", {})
        tool_name = tool_call.get("name")
        if not tool_name:
            async for chunk in await next_handler(**kwargs):
                yield chunk
            return
        if tool_name in toolkit.tools:
            tool = toolkit.tools[tool_name]
            group_name = tool.group
            if group_name and group_name != "basic":
                for g in toolkit.groups:
                    toolkit.update_tool_groups([g], active=False)
                toolkit.update_tool_groups([group_name], active=True)
        async for chunk in await next_handler(**kwargs):
            yield chunk
    return middleware