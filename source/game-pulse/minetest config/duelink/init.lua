local file_path = "gamepulse.txt"

-- Store last state per player
local last_state = {}

minetest.register_on_joinplayer(function(player)
    player:set_hp(20)

    local name = player:get_player_name()
    last_state[name] = {
        punch = -1,
        hp = -1
    }
end)

minetest.register_on_leaveplayer(function(player)
    local name = player:get_player_name()
    last_state[name] = nil
end)

minetest.register_globalstep(function(dtime)
    local players = minetest.get_connected_players()

    for _, player in ipairs(players) do
        local name = player:get_player_name()

        -- Get punch
        local punch = 0
        if player:get_player_control().LMB then
            punch = 1
        end

        -- Get HP (round to integer)
        local hp = math.floor(player:get_hp())

        local state = last_state[name]

        -- Initialize safety (in case)
        if not state then
            last_state[name] = { punch = punch, hp = hp }
            state = last_state[name]
        end

        -- ✅ Only write if ANY value changed
        if state.punch ~= punch or state.hp ~= hp then
            state.punch = punch
            state.hp = hp

            local msg = string.format("PUNCH:%d,HP:%d", punch, hp)

            local file = io.open(file_path, "w")
            if file then
                file:write(msg)
                file:close()
            end
        end
    end
end)