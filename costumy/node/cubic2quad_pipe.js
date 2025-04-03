const {parseSVG, makeAbsolute} = require('svg-path-parser');
const cubic2quad = require('cubic2quad');
var d = process.argv[2].toString()

function mRound(f){
    return Math.round(f*10)/10
    //return Math.round(f)
}

function ConvertToQuadAndLine(pathDescription,tolerance=5,round=true,verbose=false){
    const commands = parseSVG(pathDescription);
    makeAbsolute(commands); // Note: mutates the commands in place!
    var newpath =""
    
    commands.forEach(e => {
        if (e.command=="quadratic curveto"){
            var quads = [e.x0,e.y0, e.x1,e.y1, e.x,e.y]                                     // to quadratic
            if (round){quads = quads.map(function(i){return mRound(i)})}                    // round points pos
            newpath += " Q " + quads.slice(2).join(" ")
        }
        if (e.command=="curveto"){
            var quads = cubic2quad( e.x0,e.y0, e.x1,e.y1, e.x2,e.y2, e.x,e.y,tolerance)     // to quadratic
            if (round){quads = quads.map(function(i){return mRound(i)})}                    // round points pos
            newpath += " Q " + quads.slice(2).join(" ")}
            if (e.command!="curveto"&&e.command!="quadratic curveto"){
                c = "M"
                if (newpath.length>0){c="L"}
                if (round){newpath += ` ${c} ${mRound(e.x)} ${mRound(e.y)}`}
                else{newpath += ` ${c} ${e.x} ${e.y}`}
            }
        });
        newpath += " Z "
        
    return newpath
}

// print the output to be used in python
var newd= ConvertToQuadAndLine(d,tolerance=(process.argv[3]))
console.log(newd)
