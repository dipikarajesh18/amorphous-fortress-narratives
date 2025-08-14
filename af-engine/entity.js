// Entity class for the Amorphous Fortress engine
class Entity{
    // static variables

    // initializing function
    constructor(fortress, entStr=null, char=null, name="", nodes=null, edges=null){
        this.char = char;
        this.name = name;
        this.pos = [-1, -1];
        this.nodes = {};
        this.edges = {};
        this.fortress = fortress;
        this.id = this.newID();


        // set the nodes and edges if provided
        if(entStr != null)
            this.importTreeStr(entStr);
        else{
            if(nodes != null && edges != null){
                this.nodes = nodes;
                this.edges = edges;
            }
        }
        

        // initialize the current properties
        this.cur_step = 0;                          // current step agent is in the simulation
        this.cur_node = Object.keys(this.nodes)[0]; // current node the agent is in
        this.moved_edge = null;                     // the edge that was activated when the node state changed
        this.other_ent = null;                      // the other entity involved in the edge activation
        this.marked = false;                        // whether the entity is marked for death
    }

    tostr(){
        return this.char + "." + this.id;
    }


    // returns a new instance id that is not already in use
    newID(id_len=4){
   
        // generate a new id
        let id = "";
        for(let a=0;a<100;a++){         // try 100 times to generate a unique id
            id = "";
            // generate a random number between 0 and 16 and convert to hex
            for(let i=0; i<id_len; i++){
                let r = randInt(0, 16);
                id += r.toString(16);
            }


            // check if the id is already in use
            if(id in this.fortress.ENT_LIST)
                continue;
            else
                return id;
        }
        return null;
    }


    ////////////////   HELPER FUNCTIONS   ////////////////

    // picks a random position adjacent to the current position
    _randAdjPos(){
        // pick a random position adjacent to the current position
        let pos_mod = [[0,1],[0,-1],[1,0],[-1,0]];
        let rpos_i = randInt(0, pos_mod.length);
        let rpos = pos_mod[rpos_i];
        let new_pos = [this.pos[0]+rpos[0], this.pos[1]+rpos[1]];

        // check if the new position is valid
        if(this.fortress.validPos(new_pos[0], new_pos[1]))
            return new_pos;
        else
            return null;
    }

    // returns the nearest entity of a certain character (excluding this)
    _anotherEnt(entityChar){
        return this.fortress.closestEnt(this.pos[0], this.pos[1], entityChar, (entityChar == this.char ? this.id : null));
    }   

    // check if 2 positions are the same
    _samePos(pos1, pos2){
        return (pos1[0] == pos2[0] && pos1[1] == pos2[1]);
    }

    // moves the entity in a specific direction (player control)
    _dirPos(dir){
        let pos_mod = {
            "up": [0,-1],
            "down": [0,1],
            "left": [-1,0],
            "right": [1,0],
            "skip": [0,0]           // shouldn't get this o_o
        }
        let new_pos = [this.pos[0]+pos_mod[dir][0], this.pos[1]+pos_mod[dir][1]];

        // check if the new position is valid
        if(this.fortress.validPos(new_pos[0], new_pos[1]))
            return new_pos;
        else
            return null;
    }

    // returns whether the entity is on a player controlled node
    _isPlayer(){
        return inArr(this.nodes[this.cur_node].split(" ")[0], PLAYER_NODE_SET);
    }

    ////////////////   NODE FUNCTIONS   ////////////////

    

    // do nothing
    static idleAct(e){
        return;
    }

    // move in a random direction if valid
    static move(e){
        let new_pos = e._randAdjPos();
        if(new_pos != null){
            e.pos = new_pos;
            e.fortress.addLog(`[${e.char}.${e.id}] moved to ${new_pos}`);
        }
    }

    // if entity dies, remove from the fortress
    static die(e,logging=true){
        if(logging)
            e.fortress.addLog(`[${e.char}.${e.id}] died`);
        e.fortress.markEntity(e);
    }

    // if entity dies, remove from the fortress (self version)
    dieAlone(logging=true){
        this.fortress.addLog(`[${this.char}.${this.id}] died alone`);
        this.fortress.markEntity(this);
    }

    // create another instance of the entity at the specific position
    static clone(e,pos=null,logging=true){
        let new_ent = new Entity(e.fortress, null, e.char, e.name, {...e.nodes}, {...e.edges});
        new_ent.pos = pos != null ? pos : e._randAdjPos();

        // don't clone if the position is invalid
        if(new_ent.pos == null || !e.fortress.floorPos(new_ent.pos[0], new_ent.pos[1])){
            if(logging){
                // e.fortress.addLog(`[${e.char}.${e.id}] failed to clone`);
            }
            return;
        }

        // add the new entity to the fortress
        e.fortress.addEntity(new_ent);
        if(logging)
            e.fortress.addLog(`"[${e.tostr()}] cloned to [${new_ent.tostr()}] at ${new_ent.pos}`);
        return new_ent;
    }

    // if the entity takes another entity, remove from map
    static take(e, entityChar){
        let other_ent = e._anotherEnt(entityChar);
        if(other_ent){
            e.fortress.addLog(`[${e.tostr()}] took [${other_ent.tostr()}]`);
            // other_ent.dieAlone();
            e.fortress.delEntity(other_ent);
        }

    }

    // if the entity chases another entity
    static chase(e, entityChar){
        // check if the entity exists at all - otherwise don't move
        let other_ent = e._anotherEnt(entityChar);
        if(other_ent == null)
            return;

        //set the target position to the other entity's position
        let target_pos = other_ent.pos;

        // same position, don't bother
        if(target_pos[0] == e.pos[0] && target_pos[1] == e.pos[1]){     
            // console.log("Target: " + target_pos + " - this: " + e.pos);
            return;
        }


        let dir = [];
        if(target_pos[0] > e.pos[0])  // right
            dir.push([1,0]);
        else if(target_pos[0] < e.pos[0]) // left
            dir.push([-1,0]);
        if(target_pos[1] > e.pos[1])  // down
            dir.push([0,1]);
        else if(target_pos[1] < e.pos[1]) // up
            dir.push([0,-1]);
        
        // pick a random direction to move in
        let rdir_i = randInt(0, dir.length);
        let rdir = dir[rdir_i];
        let new_pos = [e.pos[0]+rdir[0], e.pos[1]+rdir[1]];

        // check if the new position is valid
        if(e.fortress.validPos(new_pos[0], new_pos[1])){
            e.pos = new_pos;
            e.fortress.addLog(`[${e.tostr()}] chased [${other_ent.tostr()}]`);
        }else{
            // console.log(e.tostr() + " cant move")
        }
    }

    // if the entity pushes another entity
    static push(e, entityChar){
        // check if the entity exists at all
        // NOTE: this is included in the python version, but the entity stops moving if the character doesn't exist
        // let ent_exists = e._anotherEnt(entityChar);
        // if(ent_exists == null)
        //     return;

        //set the target position to the other entity's position
        let pos_mod = [[0,1],[0,-1],[1,0],[-1,0]];
        let rdir = pos_mod[randInt(0, pos_mod.length)];
        let new_pos = [e.pos[0]+rdir[0], e.pos[1]+rdir[1]];
        let val_new_pos = e.fortress.validPos(new_pos[0], new_pos[1]);

        // if the new position is the same as the other entity, 
        // then push it over in the same directionif possible
        // if(e._samePos(new_pos, other_ent.pos)){
        let other_ents = e.fortress.multi_entAtPos(new_pos[0], new_pos[1]);
        let other_ent = null;
        // grab the first matching ent if available
        for(let o=0;o<other_ents.length;o++){
            if(other_ents[o].char == entityChar){
                other_ent = other_ents[o];
                break;
            }
        }
        
        if(other_ent != null && other_ent.char == entityChar){
            let new_pos_e = [other_ent.pos[0]+rdir[0], other_ent.pos[1]+rdir[1]];
            // if the new other entity position is valid, move it
            if(e.fortress.validPos(new_pos_e[0], new_pos_e[1])){
                // move the other entity
                other_ent.pos = new_pos_e;

                // move this entitya
                e.pos = new_pos;
                e.fortress.addLog(`[${e.tostr()}] pushed [${other_ent.tostr()}]`);
            }else{
                // e.fortress.addLog(`[${e.char}.${e.id}] unable to push ${other_ent.char}.${other_ent.id} to ${new_pos}`);
            }
        }else if(val_new_pos){
            // otherwise just move to the new position
            e.pos = new_pos;
            e.fortress.addLog(`[${e.tostr()}] moved to ${new_pos}`);
        }else if(!val_new_pos){
            // e.fortress.addLog(`[${e.char}.${e.id}] invalid pos: ${new_pos}`);
        }
    }

    // add another entity instance to the fortress
    static addEnt(e, entityChar){
        let new_ent_pos = e._randAdjPos();

        // check if the position is valid, can be placed, and is not occupied
        if(new_ent_pos == null 
            || !e.fortress.floorPos(new_ent_pos[0], new_ent_pos[1])){
            return;
            }

        // create the new entity
        let new_ent = e.fortress.CHAR_DICT[entityChar].copy(new_ent_pos);
        
        e.fortress.addLog(`[${e.tostr()}] added [${new_ent.tostr()}] at ${new_ent.pos}`);
    }

    // transform this entity into another entity
    static transform(e, entityChar){
        let new_ent = e.fortress.CHAR_DICT[entityChar].copy(e.pos);
        if(new_ent != null){
            e.fortress.addLog(`[${e.tostr()}] transformed into [${new_ent.tostr()}] at ${new_ent.pos}`)
            e.fortress.delEntity(e,false);
        }
    }

     
    // if entity moves and specified character is not in the way, update position
    static wall(e, entityChar){
        let new_pos = e._randAdjPos();
        if(new_pos != null){
            let other_ents = e.fortress.multi_entAtPos(new_pos[0], new_pos[1]);
            let eap = null;
            // grab the first matching ent if available
            for(let o=0;o<other_ents.length;o++){
                if(other_ents[o].char == entityChar){
                    eap = other_ents[o];
                    break;
                }
            }


            // let eap = e.fortress.entAtPos(new_pos[0], new_pos[1]);
            if(eap == null || eap.char != entityChar){
                e.pos = new_pos;
                e.fortress.addLog(`[${e.tostr()}] moved to ${new_pos}`);
            }else{
                e.fortress.addLog(`[${e.tostr()}] blocked by [${eap.tostr()}]`);
            }
        }
    }

    // same as clone above but without the passed entity parameter (uses self)
    copy(pos=null,logging=false){
        let new_ent = new Entity(this.fortress, null, this.char, this.name, {...this.nodes}, {...this.edges});
        new_ent.pos = pos != null ? pos : this._randAdjPos();

        // don't clone if the position is invalid
        if(new_ent.pos == null || !this.fortress.validPos(new_ent.pos[0], new_ent.pos[1]))
            return;

        // add the new entity to the fortress
        this.fortress.addEntity(new_ent);
        if(logging)
            this.fortress.addLog(`[${this.tostr()}] cloned to [${new_ent.tostr()}] at ${new_ent.pos}`);
        return new_ent;
    }


    // --- player movements --- //

    // move in a user-specific direction if valid
    static player_move(e, dir){

        if(dir == "skip")       // don't move
            return;

        let new_pos = e._dirPos(dir);
        if(new_pos != null){
            e.pos = new_pos;
            e.fortress.addLog(`[${e.tostr()}] moved to ${new_pos} >> PLAYER`);
        }
    }

    // if the user-controlled entity pushes another entity 
    static player_push(e, entityChar, dir){

        // check if the entity exists at all
        // NOTE: this is included in the python version, but the entity stops moving if the character doesn't exist
        // let ent_exists = e._anotherEnt(entityChar);
        // if(ent_exists == null)
        //     return;
        
        if(dir == "skip")       // don't move
            return;

        let pos_mod = {
            "up": [0,-1],
            "down": [0,1],
            "left": [-1,0],
            "right": [1,0],
        }

        // get the user position
        let new_pos = e._dirPos(dir);
        let rdir = pos_mod[dir];
        let val_new_pos = new_pos != null ? e.fortress.validPos(new_pos[0], new_pos[1]) : null;

        // if the new position is the same as the other entity, 
        // then push it over in the same direction if possible
        // if(e._samePos(new_pos, other_ent.pos)){
        let other_ents = e.fortress.multi_entAtPos(new_pos[0], new_pos[1]);
        let other_ent = null;
        // grab the first matching ent if available
        for(let o=0;o<other_ents.length;o++){
            if(other_ents[o].char == entityChar){
                other_ent = other_ents[o];
                break;
            }
        }
        if(other_ent != null && other_ent.char == entityChar){
            let new_pos_e = [other_ent.pos[0]+rdir[0], other_ent.pos[1]+rdir[1]];
            // if the new other entity position is valid, move it
            if(e.fortress.validPos(new_pos_e[0], new_pos_e[1])){
                // move the other entity
                other_ent.pos = new_pos_e;

                // move this entity
                e.pos = new_pos;
                e.fortress.addLog(`[${e.tostr()}] pushed [${other_ent.tostr()}] >> PLAYER`);
            }else{
                // e.fortress.addLog(`[${e.char}.${e.id}] unable to push ${other_ent.char}.${other_ent.id} to ${new_pos}`);
            }
        }else if(val_new_pos){
            // otherwise just move to the new position
            e.pos = new_pos;
            e.fortress.addLog(`[${e.tostr()}] moved to ${new_pos} >> PLAYER`);
        }else if(!val_new_pos){
            // e.fortress.addLog(`[${e.char}.${e.id}] invalid pos: ${new_pos}`);
        }
    }


    // if entity moves and specified character is not in the way, update position
    static player_wall(e, entityChar, dir){
        if(dir == "skip")
            return;
        let new_pos = e._dirPos(dir);
        if(new_pos != null){
            let eap = e.fortress.entAtPos(new_pos[0], new_pos[1]);
            if(eap == null || eap.char != entityChar){
                e.pos = new_pos;
                e.fortress.addLog(`[${e.tostr()}] moved to ${new_pos} >> PLAYER`);
            }else{
                e.fortress.addLog(`[${e.tostr()}] blocked by wall [${eap.tostr()}] >> PLAYER`);
            }
        }
    }



    ////////////////   EDGE FUNCTIONS   ////////////////

    // every x steps in the simulation
    static every_step(e,steps){
        // resets step counter if the current step is a multiple of the steps
        let on_step = e.cur_step % parseInt(steps);
        if(on_step == 0){
            // e.cur_step = 0;
            return true;
        }else
            return false;

        // return (e.cur_step % parseInt(steps) == 0);
    }
    
    // if the entity touches another entity with the speicified character
    static touch(e,entityChar){
        // check if the entity is a valid character
        if(!(entityChar in e.fortress.CHAR_ENT_SET))
            return false;

        for(let [i, ent] of Object.entries(e.fortress.CHAR_ENT_SET[entityChar])){
            // skip this
            if(ent.tostr() == e.tostr())
                continue;

            // check if the entity is the right character and within range
            if(ent.char == entityChar){
                if(ent.pos[0] == e.pos[0] && ent.pos[1] == e.pos[1]){
                    // console.log("TOUCHING! " + ent.char + "." + ent.id + " " + e.char + "." + e.id);
                    return true;
                }
            }
        }
        return false;
    }

    // if the entity is within x spaces of another entity
    static within(e,entityChar, range){
        // console.log("within normal")

        // check if the entity is a valid character
        if(!(entityChar in e.fortress.CHAR_ENT_SET))
            return false;

        range = parseInt(range);
        for(let [i, ent] of Object.entries(e.fortress.CHAR_ENT_SET[entityChar])){
            // skip this
            if(ent.tostr() == e.tostr())
                continue;

            // check if the entity is the right character and within range
            if(ent.char == entityChar){
                let tot_dist = Math.abs(ent.pos[0]-e.pos[0]) + Math.abs(ent.pos[1]-e.pos[1]);
                // if(Math.abs(ent.pos[0]-e.pos[0]) <= range && Math.abs(ent.pos[1]-e.pos[1]) <= range)
                if(tot_dist <= range)       // manhattan distance
                    return true;
            }
        }

        return false;
    }

    // if the entity is within x spaces of another entity (self version)
    withinSelf(entityChar, range){

        // check if the entity is a valid character
        if(!(entityChar in this.fortress.CHAR_ENT_SET)){
            // console.log("all dead!");
            return false;
        }

        range = parseInt(range);
        for(let [i, ent] of Object.entries(this.fortress.CHAR_ENT_SET[entityChar])){
            // skip self
            if(ent.tostr() == this.tostr())
                continue;

            // check if the entity is the right character and within range
            if(ent.char == entityChar){
                let tot_dist = Math.abs(ent.pos[0]-this.pos[0]) + Math.abs(ent.pos[1]-this.pos[1]);
                // console.log(this.tostr() + " + " + ent.tostr() + " = " + tot_dist)
                
                // if(Math.abs(ent.pos[0]-this.pos[0]) <= range && Math.abs(ent.pos[1]-this.pos[1]) <= range)   // euclidean distance
                if(tot_dist <= range)       // manhattan distance
                    return true;
            }
        }

        // console.log(this.char + "." + this.id + " - not in range")

        return false;
    }

    // if the entity is next to another entity
    static nextTo(e,entityChar){
        return e.withinSelf(entityChar, 1);
    }

    // none condition to change states on the next step (always true)
    static noneCond(e){
        return true;
    }


    ////////////////   GRAPH FUNCTIONS   ////////////////

    // imports a tree from a string format
    importTreeStr(s){
        // reset dicts
        this.nodes = {}
        this.edges = {}

        // split the string into lines
        let lines = s.split("\n").filter(function (l) {return l != "";});

        // parse the character
        let first_line = lines[0].split(" - ")
        this.char = first_line[0]
        if(first_line.length > 1)
            this.name = first_line[1]

        // find the breaker headers
        let node_break = lines.indexOf("-- NODES --")
        let edge_break = lines.indexOf("-- EDGES --")

        // parse the nodes
        for(let i=node_break+1; i<edge_break; i++){
            let n = lines[i].split(": ");
            this.nodes[n[0]] = n[1]
        }
        // parse the edges
        for(let i=edge_break+1; i<lines.length; i++){
            let e = lines[i].split(": ")
            this.edges[e[0]] = e[1]
        }
    }

    // exports the tree to a string format
    exportTreeStr(){
        // create the string
        let str = this.char + " - " + this.name + "\n"

        // add the nodes
        str += "-- NODES --\n"
        for(let [k, v] of Object.entries(this.nodes)){
            str += k + ": " + v + "\n";
        }
        // for(let i=0;i<this.nodes.length;i++){
        //     let n = this.nodes[i];
        //     str += i + ": " + n + "\n";
        // }

        // add the edges
        str += "-- EDGES --\n"
        for(let [k, v] of Object.entries(this.edges)){
            str += k + ": " + v + "\n";
        }

        return str
    }


    ////////////////   SIMULATION FUNCTIONS   ////////////////

    // update the behavior tree of the entity by looking at the graph and any connections
    // direction is for player control
    update(dir="random"){
        // increment the local step counter
        this.cur_step += 1;

        /////  DO THE NODE ACTION  /////

        // get the current node and its associated action
        // console.log(this.tostr() + ": " + this.cur_node + " - " + this.nodes[this.cur_node])
        let active_node = this.nodes[this.cur_node];
        let act_node_parts = active_node.split(" ");

        // set the direction for player control (if random, give a random direction)
        if(dir == "random")
            dir = randArr(["up","down","left","right","skip"]);

        // call the function 
        let func = NODE_DICT[act_node_parts[0]]["func"];

        // multi parameter function + player functions
        if(act_node_parts.length > 1 || active_node.indexOf("play_") != -1){
            let args = act_node_parts.length == 1 ? [] : act_node_parts.slice(1);

            // if the function is player based, pass the direction at the end as well
            if(inArr("dir", NODE_DICT[act_node_parts[0]]["args"]))
                args.push(dir);
                
            func(this,...args);
        }else{
            func(this);
        }


        /////  CHECK FOR EDGE ACTIVATION  /////

        // if edges are available that fulfill the condition for crossing from the current node, then do it
        // order of priority: touch, nextTo, step, within, none
        let cur_edges = [];
        for(let [k, v] of Object.entries(this.edges)){
            if(k.split("-")[0] == String(this.cur_node))
                cur_edges.push(k);
        }
        // let cur_edges = Object.keys(this.edges).filter(k => this.edges[k].split("-")[0] == String(active_node));
        // console.log(cur_edges);

        // divide the edges into priority groups O(# edges @ cur node)
        let edge_prior = [];
        for(let p=0;p<Object.keys(EDGE_DICT).length;p++){
            edge_prior.push([]);
        }
        for(let e=0;e<cur_edges.length;e++){
            let edge_p = cur_edges[e];              // edge pair
            let edge_v = this.edges[edge_p];        // edge value
            let edge_cond = edge_v.split(" ")[0];   // edge condition (type)
            edge_prior[EDGE_DICT[edge_cond]["priority"]].push(edge_p);       // add the edge to the priority group
        }

        // based on the bins enact the first possible priority - reversed order
        // worst case O(# edges @ cur_node) lower bound 1
        let updated = false;
        for(let i=edge_prior.length-1;i>-1;i--){
            // already updated, so break
            if(updated)
                break;

            for(let edge_p of edge_prior[i]){
                let edge_v = this.edges[edge_p];        // get edge condition and args
                

                // get the edge condition and args
                let cond = edge_v.split(" ")[0];      // condition
                let cond_func = EDGE_DICT[cond]["func"];   // condition function
                // console.log(edge, cond_func);
                
                // get the args
                let args = edge_v.split(" ").slice(1);    // args

                // if(args.length > 0)
                //     console.log(this.char + "." + this.id + " - " + cond_func.name + " = " + cond_func(this,...args));

                // check if the condition is met
                if(cond_func(this,...args)){
                    // update the node
                    this.cur_node = parseInt(edge_p.split("-")[1]);
                    this.moved_edge = edge_p;
                    updated = true;
                    break;
                }else{
                    this.moved_edge = null;
                }
            }
        }
        
    }

}

// associates names to the functions for the node actions the agent will perform
var NODE_DICT = {
    "idle": {"func": Entity.idleAct, "args": []},
    "move": {"func": Entity.move, "args": []},
    "die": {"func": Entity.die, "args": []},
    "clone": {"func": Entity.clone, "args": []},
    "take": {"func": Entity.take, "args": ["entityChar"]},
    "chase": {"func": Entity.chase, "args": ["entityChar"]},
    "push": {"func": Entity.push, "args": ["entityChar"]},
    "add": {"func": Entity.addEnt, "args": ["entityChar"]},
    "transform": {"func": Entity.transform, "args": ["entityChar"]},
    "move_wall": {"func": Entity.wall, "args": ["entityChar"]},

    // player action nodes
    "play_move": {"func": Entity.player_move, "args": ["dir"]},
    "play_push": {"func": Entity.player_push, "args": ["entityChar", "dir"]},
    "play_m_wall": {"func": Entity.player_wall, "args": ["entityChar", "dir"]}
}

// associates names to functions for the edge conditions that will activate the node actions
// lower number means it will happen last
var EDGE_DICT = {
    "none": {"func":Entity.noneCond, "args":[], "priority":0},
    "step": {"func":Entity.every_step, "args":["steps"], "priority":1},
    "within": {"func":Entity.within, "args":["entityChar","range"], "priority":2},
    "nextTo": {"func":Entity.nextTo, "args":["entityChar"], "priority":3},
    "touch": {"func":Entity.touch, "args":["entityChar"], "priority":4}
}