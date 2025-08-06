// constants characters
const FORBID_CHARS = [".", "<", "_", "#", "-", "\\", ":"]        // forbidden characters
const FLOOR_CHAR = ".";
const WALL_CHAR = "#";
const FORT_WIDTH = 16;
const FORT_HEIGHT = 8;

const ALL_FONTS = ["JetbrainsBold","Proggy","IBM_Alt3","Courier","Fixedsys","monospace"];
const FONT_LOAD_DELAY = 250;    // delay in ms to load fonts    

const MAX_ENT_FORT = 20;        // maximum number of entities definitions allowed for a fortress
const MAX_INT_PARAM = 20;       // maximum number of values for the edge condition drop down parameter
const MAX_ENT_BACKPACK = 10;    // maximum number of entities definitions allowed for the backpack

const RAND_DAILY_OBJS = ["table","chair","car","book","phone","tree","cup","dog","cat","house","bicycle","wallet","shoe","spoon","door","hat","flower","pen","television","backpack"];
const RAND_DUNGEON_OBJS = ["chest","skeleton","torch","rat","spider","potion","scroll","goblet","key","knight","goblin","monster","dragon"]
const RAND_ANIMALS = ["bird","fish","frog","snake","horse","rabbit","mouse","deer","lion","tiger","bear","owl","bat","koala","panda","goat","fox","wolf"]
const RAND_SET = RAND_DAILY_OBJS.concat(RAND_DUNGEON_OBJS,RAND_ANIMALS);
const RAND_SYMB = ["%","$","@","!","*","&","?","+","=","}"]

const ACTION_NODE_SET = ["idle", "move", "die", "clone", "take ?", "chase ?", "push ?", "add ?", "transform ?", "move_wall ?", "play_move", "play_push ?", "play_m_wall ?"];
const COND_EDGE_SET = ["none", "step #", "within ? #", "nextTo ?", "touch ?"];
const PLAYER_NODE_SET = ["play_move", "play_push", "play_m_wall"];

const DEFAULT_FONT = "JetbrainsBold";
const DEFAULT_USER = "dork";
const DEFAULT_SEED = "Hello world!";

const SITE_VERSION = "v.1";


//////////////////////////   GENERAL FUNCTIONS     /////////////////////////


// checks if an element is in an array
function inArr(e, arr){
    return arr.indexOf(e) != -1;
}

// removes an element (based on value) from an array
function removeArr(e,arr,all_inst=false){
    for(let i=0;i<arr.length;i++){
        if(arr[i] == e){
            arr.splice(i,1);
            if(!all_inst)
                return;
        }
    }
}


// check if a position is [o]ut [o]f [b]ounds (either value is -1)
function oob(pos){
    return pos[0] == -1 || pos[1] == -1;
}

// return random number between range
function randNum(min,max){
    return Math.floor(Math.random()*(max-min))+min
}

// randomly pick one thing from an array
function randArr(arr){
    return arr[Math.floor(Math.random()*arr.length)]
}

// returns a random integer between min and max inclusive
function randInt(min, max){
    return parseInt((Math.random() * (max - min)) + min);
  }

// randomly shuffle an array
function shuffleArr(arr){
    return arr.sort(() => .5 - Math.random());
}

// checks if a position is [o]utside [o]f a bounding [b]ox [b]oundary
// pos = obj{x,y}
// box = obj{x,y,w,h}
function oobb(pos, box){
    if((pos.x < box.x) || (pos.x > (box.x+box.w)))
        return true;
    else if((pos.y < box.y) || (pos.y > (box.y+box.h)))
        return true;
    else
        return false;
}

// returns whether an array of positions contains a particular position
// note: must have same format
function hasPos(pos, arrPos){
    for(let a=0;a<arrPos.length;a++){
        let ai=arrPos[a];
        if(ai[0] == pos[0] && ai[1] == pos[1])
            return a;
    }
    return -1;
}

// regex matches a pattern (bool)
function regMatch(str, pat){
    return str.search(pat) != -1;
}

// regex extracts a pattern (str)
function regExt(str, pat){
    return str.match(pat)
}


//////////////////////////   EDGE FUNCTIONS     /////////////////////////


// converts a string edge to integer pair
function edge2pair(e){
    let ep = e.split(": ")[0].split("-");
    let ea = parseInt(ep[0]);
    let eb = parseInt(ep[1]);
    return [ea,eb];
}

function oppEdge(e){
    let ep = edge2pair(e);
    return ep[1] + "-" + ep[0];
}


// sorts edges (a then b numerically)
function edgeSort(a,b){
    let ap = a.split(": ")[0].split("-");
    let bp = b.split(": ")[0].split("-");
    ap = ap.map((x) => parseInt(x));
    bp = bp.map((x) => parseInt(x));
    return ((ap[0] == bp[0]) ? (ap[1] - bp[1]) : (ap[0] - bp[0]));
}

// binary search on edges
// do it for the user
function edgeBinSearch (array, key, start, end) {
    if(start === end){
        if(edgeSort(array[start],key) > 0){
            return start
        }else{
            return start + 1
        }
    }
  
    if(start > end){
        return start
    }
  
    const mid = Math.floor((start + end) / 2)
  
    if(edgeSort(array[mid], key) < 0){
        return edgeBinSearch(array, key, mid + 1, end)
    }else if(edgeSort(array[mid],key) > 0){
        return edgeBinSearch(array, key, start, mid - 1)
    }else{
        return mid
    }
}

// inserts an edge with binary sort O(logn)
function edgeBinInsertSort(edge_arr,e,add=true){
    const totalLength = edge_arr.length;
    const i = edgeBinSearch(edge_arr,e,0,totalLength-1);
    if(add)
        edge_arr.splice(i,0,e);
    return i;
}


//////////////////////////  POSITION FUNCTIONS     /////////////////////////


// converts cartesian x,y positions to chess positions (#,a-z)
// row = number, col = a-z (offset by 1)
function cart2Chess(pos){
    return [pos[0],String.fromCharCode(96 + pos[1])];
}
// reverse of above
function chess2Cart(pos){
    return [pos[0],pos[1].charCodeAt(0)-96]
}




//////////////////////////   MATH BULLSHIT FUNCTIONS     /////////////////////////


// radians to degrees converter
function rad2deg(rad){
    return rad * (180/Math.PI);
}

// degrees to radians converter
function deg2rad(deg){
    return deg * (Math.PI/180);
}

// returns the slope of the line between two points
function getSlope(a,b){
    return (b.y - a.y) / (b.x - a.x);
}

// returns the distance between two points
function dist(a,b){
    return Math.sqrt(Math.pow(b.x-a.x,2) + Math.pow(b.y-a.y,2));
}

// calculates the perpendicular bisectors of two points
// for use with the edge quadratic curve
function getPerpBisectors(a,b,d=null){
    // 1. get the slope of ab
    let slope = getSlope(a,b);

    // 2. get the midpoint of ab
    let mid = {
        x: (a.x + b.x) / 2,
        y: (a.y + b.y) / 2
    }

    // 3. get the perpendicular slope
    let perp_slope = null;
    if(slope == 0){
        perp_slope = Infinity;
    }else if(slope == Infinity){
        perp_slope = 0;
    }else{
        perp_slope = -1/slope;
    }

    // 4. find the alternative points based on the cos/sin right angle triangle
    d = d == null ? dist(a,mid)/2 : d;  //distance between a and mid
    let ang = Math.atan(perp_slope);  // angle between the perpendicular bisector slope and the x-axis
    let dx = d*Math.cos(ang);   
    let dy = d*Math.sin(ang);

    let alt_points = [
        {x:mid.x+dx, y:mid.y+dy},
        {x:mid.x-dx, y:mid.y-dy}
    ]
    return alt_points;
}

// check if 2 line segments intersect
// a = [p1,p2], b = [p3,p4]
function crosses(a,b){
    return ccw(a[0],b[0],b[1]) != ccw(a[1],b[0],b[1]) && ccw(a[0],a[1],b[0]) != ccw(a[0],a[1],b[1]);
}

// idfk copilot wrote this
function ccw(a,b,c){
    return (c.y-a.y)*(b.x-a.x) > (b.y-a.y)*(c.x-a.x);
}




//////////////////////////     SITE FUNCTIONS     /////////////////////////


// change the current page
function loadPage(page){
    document.location.href = page;
}

// open the window in a new tab
function newPage(page){
    window.open(page, "_blank");
}

// load the main screen with a specific parameter
function gotoMain(pageType, val){
    window.location.href = "index.php?" + pageType + "=" + val;
    // console.log("going to main: " + pageType + "=" + val);
}

// load the main screen but confirm
function confirmBack(){
    if(confirm("Are you sure you want to go back? All unsaved changes will be lost.")){
        loadPage("index.php");
    }
}



// sets the local storage to the currently selected fortress
function setCurFort_losto(fort){
    localStorage.setItem("CUR_FORTRESS", JSON.stringify(fort));
}

// retrieves the data of the current fortress from the local storage
function retrCurFort_losto(){
    // if the current fortress key exists, return it
    if("CUR_FORTRESS" in localStorage && localStorage.getItem("CUR_FORTRESS") != null){
        return JSON.parse(localStorage.getItem("CUR_FORTRESS"));

    // current fortress key not set yet, so set it but return null
    }else{
        localStorage.setItem("CUR_FORTRESS", newFortJSON());
        return null;
    }
}

// removes the current fortress in the local storage
function removeCurFort_losto(){
    localStorage.setItem("CUR_FORTRESS", null);
}

// creates a blank fortress json object (for use with database)
function newFortJSON(){
    let cur_date = new Date();
    let date_str = cur_date.getFullYear() + "-" + (cur_date.getMonth()+1) + "-" + cur_date.getDate();

    let new_fort = {
        "fort_id":-1,
        "name":"Dork Fortress",
        "author":CURRENT_USER,  
        "fort_def_str":"@ - Dork\n-- NODES --\n0: idle\n-- EDGES --\n0-0: none\n\n-- INIT FORT --\n###############\n#.............#\n#.............#\n#.............#\n#.............#\n#.............#\n#.............#\n###############",
        "dimensions":[15,8],         
        "notes":"A simple fort for dorks",
        "seed":"__RANDOM__",                
        "date_made":date_str,                  
        "fort_remix_id":-1,
        "ent_remixes":[],
        "play_ct":0,
        "node_graph_pos_set":"{}"
    }
    return JSON.stringify(new_fort);
}

// sets a value in the fortress data object in the local storage
// for use with the database
function setFortDatValue_losto(key, value){
    let fort = retrCurFort_losto();
    fort[key] = value;
    setCurFort_losto(fort);
}

// gets a value in the fortress data object in the local storage
function getFortDatValue_losto(key){
    let fort = retrCurFort_losto();
    return fort[key];
}

// checks whether the fortress has a game node ("play_")
function fortHasGameNode(){
    let fort = retrCurFort_losto();
    if("fort_def_str" in fort)
        return regMatch(fort["fort_def_str"],"play_");
    return false;
}
