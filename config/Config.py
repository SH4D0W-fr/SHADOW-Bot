ServerID = 1460609497344250085
ServerName = "SHADOW Dev"


WelcomeChannelID = 1460637521695211662
WelcomeMessage = "Bienvenue sur le serveur, {member}!"
GoodbyeChannelID = 1460637539563208714
GoodbyeMessage = "Au revoir, {member} ! Tu vas nous manquer."

Logs = {
    # Bot features
    "giveaway": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    
    # Tickets
    "ticket_create": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_claim": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_close": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_delete": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_rename": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_member_add": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_member_remove": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "ticket_autoclose": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },

    # Messages
    "message_delete": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "message_edit": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "message_bulk_delete": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    
    # Modération
    "member_ban": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "member_kick": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "member_timeout": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "member_unban": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    
    # Voix
    "voice_join": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "voice_leave": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "voice_move": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "voice_mute": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "voice_deafen": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    
    # Serveur
    "channel_create": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "channel_delete": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "channel_update": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "role_create": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "role_delete": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "role_update": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "member_role_update": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "member_nickname_change": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    
    # Invitations
    "invite_create": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
    "invite_delete": {
        "enabled": True,
        "channel_id": 1461276988865253500
    },
}

TicketChannel = 1461708320434950335

TicketAutoPingRole = 1461709099774509169 # When users with this role send a message, the bot will ping the author of the ticket

TicketAutoCloseDelay = 12  # Auto close time when a staff answer and ther isnt response from user, in hours

TicketTypes = {
    "test1": {
        "name": "Test 1",
        "description": "Description du ticket de test 1",
        "category_id": 1461708362042314938,
        "staff_roles_id": [1461708434402443274, 1461709099774509169],
        "roles_to_ping": [1461708434402443274]
    },
    "test2": {
        "name": "Test 2",
        "description": "Description du ticket de test 2",
        "category_id": 1461708362042314938,
        "staff_roles_id": [1461708434402443274, 1461709099774509169],
        "roles_to_ping": [1461708434402443274]
    }
}