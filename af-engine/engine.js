// Engine class for the Amorphous Fortress engine
class Engine{
    constructor(config, fort_str=null, init_seed=null){
        this.config = config;

        // initialize the random number generator
        if(init_seed != null)
            this.seed = init_seed;
        else if(this.config.seed != null && this.config.seed != "__RANDOM__")
            this.seed = this.config.seed;
        else
            this.seed = Math.floor(Math.random()*2147483647);


        // define the fortress
        this.width = this.config.width ? this.config.width : 15;
        this.height = this.config.height ? this.config.height : 8;
        this.fort_str = fort_str;
        this.fortress = new Fortress(this.seed, this.width, this.height, fort_str);     
        
        // setup the engine
        this.sim_tick = 0;

    }

    // updates the state of the fortress through the engine
    update(tree_visit=false, dir=null){
        // check end condition
        if(this.fortress.terminate_fortress(this.config.inactive_limit || 100))
            return 0;

        // increment the simulation step
        this.sim_tick++;
        this.fortress.steps = this.sim_tick;

        // starting entities
        let cur_ents = Object.values(this.fortress.ENT_LIST);

        // update all of the entities
        for(let e=0; e<cur_ents.length; e++){
            let entity = cur_ents[e];

            // died so skip
            if(Object.keys(this.fortress.ENT_LIST).indexOf(entity.id) == -1)
                continue;

            // update the entity
            entity.update(dir);
            // console.log(`${entity.id}-${entity.char}`);

            if(tree_visit)
                this.fortress.addTreeVisit(entity);
            
        }

        // kill entities marked for death
        for(const entity of Object.values(this.fortress.ENT_LIST)) {
            if(entity.marked){
                this.fortress.delEntity(entity);
            }
        }

        return 1;
    }

    // reset the fortress to its initial state
    // reset the seed too
    reset(){
        this.fortress.setSeed(this.fortress.seed,true);
        this.sim_tick = 0;
    }

    // set fortress based on input string
    setFortress(dat_str){
        this.fort_str = dat_str;
        this.fortress = new Fortress(this.seed, this.width, this.height, dat_str);
        this.sim_tick = 0;
        return this.fortress;
    }

    // returns entities currently in player control
    getPlayerEnts(){
        let player_ents = [];
        for(const entity of Object.values(this.fortress.ENT_LIST)) {
            if(inArr(entity.nodes[entity.cur_node].split(" ")[0], PLAYER_NODE_SET)){
                player_ents.push(entity.id);
            }
        }
        return player_ents;
    }

    // if the simulation should wait for player input
    waitForPlayer(){
        return this.getPlayerEnts().length > 0
    }
}