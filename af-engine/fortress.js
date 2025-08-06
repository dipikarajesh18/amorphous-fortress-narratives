// Fortress class for the Amorphous Fortress engine
class Fortress{
    constructor(seed, width, height, data=null){
        // base information
        this.seed = seed;
        this.width = width;
        this.height = height;
        this.MAX_ENTITIES = (width-2)*(height-2)*2;
    
        // entity information
        this.ENT_LIST = {};                // maintains set of entity instances by id
        this.CHAR_DICT = {};               // FSM definitions for the entity classes
        this.CHAR_VISIT_TREE = {};         // visit tree for the entity characters (at class level)
        this.CHAR_ENT_SET = {};            // maintains list of entity instances by class

        this.fortMap = this.blankFortress();                                        // fortress map
        this.initStr = null;                                                        // initial fortress state string

        // background setup
        // this.rng = randomAF(this.seed);                                           // initialize the random number generator
        // this.setSeed(this.seed);                                                    // initialize the random number generator
        this.log = [];                                                             // initialize the log
        this.end_cause = null;
        this.steps = 0;                                                              // initialize the step counter
        // fortress setup        
        if(data != null){                       // import from string
            this.importFortStr(data);
        }else{
            // add fortress randomizer code here
        }
        this.setSeed(this.seed);
        // this.initLog();
    }


    ////////////////   FORTRESS SETUP FUNCTIONS   ////////////////


    // returns a blank fortress
    blankFortress(){
        let fortMap = [];
        for(let i=0; i<this.height; i++){
            fortMap.push([]);
            for(let j=0; j<this.width; j++){
                // add walls around the edge
                if(i==0 || i==this.height-1 || j==0 || j==this.width-1)
                    fortMap[i].push(WALL_CHAR);
                // otherwise add floors
                else
                    fortMap[i].push(FLOOR_CHAR);
            }
        }
        return fortMap;
    }

    // sorts 2 entities depending on the size of their node graphs
    sizeEntSort(a,b){
        let an = Object.keys(a.nodes).length;
        let bn = Object.keys(b.nodes).length;
        if(an < bn)
            return -1;
        else if(bn < an)
            return 1;
        else
            return 0;
    }

    // returns a 2D character representation of the fortress map with entities
    fort2D(){
        // add the entities to the map
        let fortEntMap = this.blankFortress();
        let entList = Object.values(this.ENT_LIST);

        // order the entities with idle nodes as cur_node last
        entList.sort(this.sizeEntSort);

        // show the fortress as a 2d array
        for(let e=0; e<entList.length; e++){
            let entity = entList[e];
            fortEntMap[entity.pos[1]][entity.pos[0]] = entity.char;
        }

        // return the map
        return fortEntMap;
    }

    // returns a string representation of the fortress map with entities
    fortString(){
        // add the entities to the map
        let fortEntMap = this.fort2D();

        // convert the map to a string
        let fortStr = "";
        for(let row of fortEntMap){
            fortStr += row.join("") + "\n";
        }

        // return the string
        return fortStr;
    }

    // parse a fortress from a string
    importFortStr(s){
        // reset everything
        this.CHAR_DICT = {};
        this.CHAR_VISIT_TREE = {};
        this.CHAR_ENT_SET = {};
        this.ENT_LIST = {};
        this.fortMap = this.blankFortress();

        // parse the fortress string
        let ent_sets = s.split("\n\n");
        
        // add each definition to the dictionary set
        for(let i=0;i<ent_sets.length;i++){
            let estr = ent_sets[i].trim();
            // console.log(estr);

            if(estr.length == 0)
                continue;

            // entity positions
            if(estr.indexOf("-- INIT ENT POS --") != -1){
                console.log("> Importing fortress by positions");
                if(Object.keys(this.ENT_LIST).length == 0)
                    this.setFortStateStr(estr, "pos");
                this.initStr = estr;
            }
            // import the fortress setup initial state
            else if(estr.indexOf("-- INIT FORT --") != -1){
                console.log("> Importing fortress by string state");
                if(Object.keys(this.ENT_LIST).length == 0)
                    this.setFortStateStr(estr, "fort");
                this.initStr = estr;
            }
            // another state of the fortress, skip
            else if(estr.indexOf("FORT") != -1){
                continue;
            }
            // import the entity class definition
            else{
                let ent = new Entity(this,estr);
                this.CHAR_DICT[ent.char] = ent;
                this.CHAR_VISIT_TREE[ent.char] = {"nodes":[], "edges":[]};

                // console.log(ent);
            }
        }

        // set the fort map to the current state
        this.fortMap = this.fort2D();
    }

    // set the fortress state from a string
    setFortStateStr(s, type_init){
        // remove all current entity instances
        this.ENT_LIST = {};

        // reset the visits
        this.resetTreeVisits();

        // parse the fortress string
        let init_ents = null;
        if(type_init == "fort")
            init_ents = this.fortStr2EntPos(s);
        else if(type_init == "pos")
            init_ents = this.posStr2EntPos(s);

        // console.log(init_ents);

        // add the entities to the fortress
        for(let i=0; i<init_ents.length; i++){
            let e = init_ents[i];
            this.CHAR_DICT[e["char"]].copy(e["pos"]);       // adds an instance of the entity to the fortress at specified position via clone
        }
    }

    // set the fortress based on a string representation
    fortStr2EntPos(s){
        let pos_set = [];
        let rows = s.split("\n");
        rows = rows.slice(1,rows.length);     // remove header

        // set the fortress dimensions and a blank map
        let dim = rows[0].split("");
        this.width = dim.length;
        this.height = rows.length;
        this.fortMap = this.blankFortress();

        // iterate through each character of the fortress string
        for(let r=0;r<rows.length;r++){
            let cur_row = rows[r].split("");
            for(let c=0;c<cur_row.length;c++){
                let char = cur_row[c];
                // skip special characters
                if(char == "\n" || char == FLOOR_CHAR || char == WALL_CHAR)
                    continue;
                // save a position for the entity if it is a valid character
                if(char in this.CHAR_DICT){
                    pos_set.push({"char":char, "pos":[c,r]});
                }
            }
        }
        return pos_set;
    }

    // set the fortress based on the entity instance position list
    posStr2EntPos(s){
        let pos_set = [];
        let lines = s.split("\n");
        lines = lines.slice(1,lines.length);      // remove header
        for(let l=0; l<lines.length; l++){
            let line = lines[l].trim();
            if(line.length == 0)
                continue;
            let d = line.split("-");
            let char = d[0];
            let pos = d[1].replace(/\[\]/g,'').split(", ").map(x => parseInt(x));
            pos_set.push({"char":char, "pos":pos});
        }
        return pos_set;
    }

    // export the entity position as a string list
    exportEntPosList(){
        let init_ents = [];
        for (let ent in Object.values(this.ENT_LIST)){
            init_ents.push(`${ent.char}-${ent.pos}`);
        }
        return init_ents;
    }

    // resets the fortress state based on the saved initial string
    resetFortress(){
        if(this.initStr == null)
            return;

        // reset everything
        this.CHAR_VISIT_TREE = {};
        this.CHAR_ENT_SET = {};
        for(let c in this.CHAR_DICT){
            this.CHAR_VISIT_TREE[c] = {"nodes":[], "edges":[]};
            this.CHAR_ENT_SET[c] = [];
        }
        this.ENT_LIST = {};
        this.fortMap = this.blankFortress();
        Math.seedrandom(this.seed);
        this.log = [];                          // initialize the log
        this.initLog();
        this.steps = 0;                                                              // initialize the step counter
        this.end_cause = null;

        // import the fortress setup initial state
        let estr = this.initStr;

        // use positions
        if(estr.indexOf("-- INIT ENT POS --") != -1){
            console.log("> Reseting initial fortress state by positions");
            if(Object.keys(this.ENT_LIST).length == 0)
                this.setFortStateStr(estr, "pos");
        }
        // use fortress
        else if(estr.indexOf("-- INIT FORT --") != -1){
            console.log("> Reseting initial fortress state by string state");
            if(Object.keys(this.ENT_LIST).length == 0)
                this.setFortStateStr(estr, "fort");
        }else{
            console.log("ERROR: No initial fortress state found.");
        }

        // set the fort map to the current state
        this.fortMap = this.fort2D();

    }

    ////////////////   POPULATION FUNCTIONS   ////////////////

    // no entities left - fortress is empty
    extinction(){
        if(Object.keys(this.ENT_LIST).length == 0){
            if(this.end_cause == null){
                this.end_cause = "extinction";
                this.addLog("[FORTRESS TERMINATED] End cause: Extinction");
            }
            return true;
        }
        return false;
    }

    // check if no activity has occured in the fortress (based on log information)
    inactive(limit=20){
        // check if over time from never doing anything
        if(this.log.length < 4 && this.steps > limit){
            if(this.end_cause == null){
                this.end_cause = "inactivity";
                this.addLog("[FORTRESS TERMINATED] End cause: Inactivity");
            }
            return true;
        }

        // check if over time from last activity
        let last_log = this.log[this.log.length-1];
        let p = /<(\d+)>/;
        let find_time = last_log.match(p);
        let last_time = find_time == null ? null : find_time[1];
        if(last_time != null && ((this.steps - parseInt(last_time)) > limit)){
            if(this.end_cause == null){
                this.end_cause = "inactivity";
                this.addLog("[FORTRESS TERMINATED] End cause: Inactivity");
            }
            return true;
        }

        return false;
    }

    // check if the fortress is full
    overpop(){
        if(Object.keys(this.ENT_LIST).length >= this.MAX_ENTITIES){
            if(this.end_cause == null){
                this.end_cause = "overpopulation";
                this.addLog("[FORTRESS TERMINATED] End cause: Overpopulation");
            }
            return true;
        }
        return false;
    }

    // check if the fortress has finished
    terminate_fortress(act_limit=20){
        return (this.extinction() || this.inactive(act_limit) || this.overpop());
    }


    ////////////////   LOG FUNCTIONS   ////////////////

    // start the log with seed and time
    initLog(){
        let d = new Date().toLocaleString("en-US", {timeZone: "America/New_York"});
        this.log = [`=====    FORTRESS SEED [${this.seed}]    =====`, "Fortress initialized! - <0>", `>>> TIME: ${d} <<<`];
    }

    // add to log
    addLog(t){
        this.log.push(`<${this.steps}> ${t}`);
    }

    // print the log to the console
    printLog(last_n=-1){
        if(last_n == -1)
            console.log(this.log.join("\n"));
        else
            console.log(this.log.slice(-last_n).join("\n"));
    }

    // export the log as a string
    exportLog(){
        let log_str = "";
        for(let i=0; i<this.log.length; i++){
            log_str += this.log[i] + "\n";
        }
        return log_str.trim();
    }

    ////////////////   ENTITY FUNCTIONS   ////////////////

    // add an instance of entity
    addEntity(ent){
        // add the entity to the entity list
        this.ENT_LIST[ent.id] = ent;

        // add the entity to the entity class list
        if(ent.char in this.CHAR_ENT_SET)
            this.CHAR_ENT_SET[ent.char].push(ent);
        else
            this.CHAR_ENT_SET[ent.char] = [ent];
    }

    // marks an entity for death (to kill later)
    markEntity(ent){
        // check if the instance exists
        if(!(ent.id in this.ENT_LIST))
            return;

        ent.marked = true;
    }

    // delete an instance of entity
    delEntity(ent){
        // check if the instance exists
        if(!(ent.id in this.ENT_LIST))
            return;

        // find the index of the entity in the char ent set
        let e_ind = this.CHAR_ENT_SET[ent.char].map((x) => x.id).indexOf(ent.id);

        // remove the entity from the entity list
        delete this.ENT_LIST[ent.id];

        if(e_ind == -1 || e_ind == null)
            console.log("ERROR: CAN'T FIND INDEX OF ID " + ent.tostr() + " IN CHAR_ENT_SET");

        // remove the entity from the entity class list
        this.CHAR_ENT_SET[ent.char].splice(e_ind, 1);
    }

    // add a visit to the character class def visitation tree
    addTreeVisit(ent){
        this.CHAR_VISIT_TREE[ent.char]["nodes"].push(ent.cur_node);
        if(ent.moved_edge != null)
            this.CHAR_VISIT_TREE[ent.char]["edges"].push(ent.moved_edge);
    }

    // reset all the tree visits per entity class
    resetTreeVisits(){
        for(let c in this.CHAR_VISIT_TREE){
            this.CHAR_VISIT_TREE[c]["nodes"] = [];
            this.CHAR_VISIT_TREE[c]["edges"] = [];
        }
    }


    ////////////////   HELPER / AUX FUNCTIONS   ////////////////

    // sets the seed value for the fortress and the rng
    setSeed(seed, reset=true){
        this.seed = seed;
        Math.seedrandom(this.seed);

        // test seed - should be the same everytime
        for(let i=0;i<3;i++)
            console.log(Math.random());

        // reset the fortress
        if(this.initStr != null && reset)
            this.resetFortress();
    }

    // check if the given position is a valid position in the fortress
    validPos(x,y){
        if(x<0 || x>=this.width || y<0 || y>=this.height)
            return false;
        return this.fortMap[y][x] != WALL_CHAR;
    }
     // check if the given position is a floor position in the fortress
    floorPos(x,y){
        if(x<0 || x>=this.width || y<0 || y>=this.height)
            return false;
        return this.fort2D()[y][x] == FLOOR_CHAR;
    }

    // returns a random position (x,y) in the fortress (optional: one not occupied by an entity)
    randomPos(inc_ent=true){
        if(!inc_ent){
            return [randInt(1,this.width-1), randInt(1,this.height-1)];
        }
        else{
            let all_pos = [];
            // get all spaces
            for(let i=1; i<this.height-1; i++){
                for(let j=1; j<this.width-1; j++){
                    if(this.fort2D()[i][j] == FLOOR_CHAR){
                        all_pos.push(`${j},${i}`);
                    }
                }
            }

            // remove occupied spaces
            let entList = Object.values(this.ENT_LIST);
            for(let e=0; e<entList.length; e++){
                let entity = entList[e];
                let ep = `${entity.pos[0]},${entity.pos[1]}`;
                all_pos.splice(all_pos.indexOf(ep), 1);
            }

            // no spaces left
            if(all_pos.length == 0)
                return null;

            // pick random unoccupied space
            let rp = all_pos[randInt(0,all_pos.length)].split(",");
            return rp;
        }
    }

    // check if the given position is occupied by an entity
    entAtPos(x,y){
        let entList = Object.values(this.ENT_LIST);
        for(let e=0; e<entList.length; e++){
            let entity = entList[e];
            if(entity.pos[0] == x && entity.pos[1] == y)
                return entity;
        }
        return null;
    }

    // returns all entities at a position
    multi_entAtPos(x,y){
        let entList = Object.values(this.ENT_LIST);
        let ents = [];
        for(let e=0; e<entList.length; e++){
            let entity = entList[e];
            if(entity.pos[0] == x && entity.pos[1] == y)
                ents.push(entity);
        }
        return ents;
    }

    // find the closest entity character from a specific position
    closestEnt(x,y,c,eid=null){
        let entList = this.CHAR_ENT_SET[c];
        let closest = null;
        let closest_dist = null;
        for(let e=0; e<entList.length; e++){
            let entity = entList[e];
            if(entity.id == eid)
                continue;
            let dist = Math.abs(entity.pos[0]-x) + Math.abs(entity.pos[1]-y);
            if(closest == null || dist < closest_dist){
                closest = entity;
                closest_dist = dist;
            }
        }
        return closest;
    }

    // check if a player controlled entity is at the specific position
    playerEntAtPos(x,y){
        let entList = Object.values(this.ENT_LIST);
        for(let e=0; e<entList.length; e++){
            let entity = entList[e];
            if(entity._isPlayer() && entity.pos[0] == x && entity.pos[1] == y)
                return [true, entity.char];
        }
        return [false,""];
    }
    
}