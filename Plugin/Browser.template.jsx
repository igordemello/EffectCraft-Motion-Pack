// Original ScriptUI extension for EffectCraft 0.21.0. MIT.
var IGPACK_MOTION;
(function (host) {
    var DATA = __IGPACK_DATA__;
    var ASSETS = "__IGPACK_ASSET_ROOT__";
    var TICKS = 254016000000;
    var state = {visible: [], current: null, frame: 0, task: null, playing: true};
    var categories = ["Todas as categorias", "Transições", "Câmera e movimento", "Glitch e distorção", "Texto", "Pop, bounce e escala", "Blur, flash e glow"];
    var ui = host instanceof Panel ? host : new Window("palette", "IGPACK Motion Browser", undefined, {resizeable: true});
    ui.orientation = "column";
    ui.alignChildren = ["fill", "top"];
    ui.margins = 16;
    ui.spacing = 10;
    var title = ui.add("statictext", undefined, "IGPACK  /  MOTION BROWSER");
    title.graphics.font = ScriptUI.newFont("Segoe UI", ScriptUI.FontStyle.BOLD, 20);
    ui.add("statictext", undefined, "98 efeitos  ·  precomps editáveis  ·  EffectCraft 0.21.0");
    var filters = ui.add("group");
    filters.orientation = "row";
    var search = filters.add("edittext", undefined, "", {name: "search"});
    search.preferredSize = [310, 28];
    search.helpTip = "Buscar por nome: zoom, glitch, bounce…";
    var category = filters.add("dropdownlist", undefined, categories, {name: "category"});
    category.selection = 0;
    category.preferredSize = [270, 28];
    var body = ui.add("group");
    body.orientation = "row";
    body.alignChildren = ["fill", "top"];
    var library = body.add("listbox", undefined, [], {name: "library"});
    library.preferredSize = [255, 400];
    var right = body.add("group");
    right.orientation = "column";
    right.alignChildren = ["fill", "top"];
    right.preferredSize = [350, 400];
    var selectedName = right.add("statictext", undefined, "Escolha um efeito", {name: "selectedName"});
    selectedName.graphics.font = ScriptUI.newFont("Segoe UI", ScriptUI.FontStyle.BOLD, 16);
    var preview = right.add("image", undefined, undefined, {name: "preview"});
    preview.preferredSize = [320, 180];
    var playback = right.add("group");
    var play = playback.add("button", undefined, "Pausar preview", {name: "play"});
    var meta = playback.add("statictext", undefined, "Prévia original", {name: "meta"});
    var mode = right.add("dropdownlist", undefined, ["Sobrepor à imagem (precomp de ajuste)", "Animar seleção (nova precomp)"], {name: "mode"});
    mode.selection = 0;
    var controls = right.add("group");
    controls.add("statictext", undefined, "Duração (s)");
    var duration = controls.add("edittext", undefined, "0.6", {name: "duration"});
    duration.preferredSize = [60, 25];
    controls.add("statictext", undefined, "Intensidade (%)");
    var strength = controls.add("edittext", undefined, "100", {name: "strength"});
    strength.preferredSize = [55, 25];
    var note = right.add("statictext", undefined, "", {name: "note", multiline: true});
    note.preferredSize = [340, 44];
    var apply = right.add("button", undefined, "Adicionar à timeline", {name: "apply"});
    apply.preferredSize = [340, 32];
    var status = ui.add("statictext", undefined, "Abra uma composição. Escolha um efeito para começar.", {name: "status", multiline: true});
    status.preferredSize = [610, 46];

    function clone(v) { return JSON.parse(JSON.stringify(v)); }
    function walk(g, prefix, visit) {
        for (var i = 0; i < g.children.length; i++) {
            var p = g.children[i], path = prefix + p.match;
            if (p.node === "Prop") visit(path, p);
            else walk(p, path + "/", visit);
        }
    }
    function framePath(item, index) {
        return ASSETS + "/" + ("00" + item.id).slice(-3) + "/" + ("0" + index).slice(-2) + ".png";
    }
    function updateImage() {
        if (state.current) preview.image = ScriptUI.newImage(framePath(state.current, state.frame));
    }
    function tick() {
        if (!state.playing || !state.current || !ui.visible) return;
        var elapsed = (new Date().getTime() - state.previewStart) / 1000;
        var d = state.current.duration;
        var phase = elapsed % (d + 0.5);
        state.frame = Math.min(12, Math.floor(phase / d * 12));
        updateImage();
    }
    function select() {
        var entry = library.selection;
        if (!entry || !state.visible[entry.index]) return;
        state.current = state.visible[entry.index];
        state.frame = 0;
        state.previewStart = new Date().getTime();
        selectedName.text = state.current.name;
        duration.text = String(state.current.duration);
        meta.text = "Original · " + state.current.duration + " s";
        mode.selection = state.current.category === 3 || state.current.category === 4 ? 1 : 0;
        modeChanged();
        updateImage();
    }
    function modeChanged() {
        note.text = mode.selection && mode.selection.index === 1 ?
            "Agrupa as camadas selecionadas.\nEdite o conteúdo dentro da precomp." :
            "Cria um clipe de efeito por cima.\nMova, duplique ou remova na timeline.";
    }
    function filter() {
        var query = search.text.toLowerCase();
        var cat = category.selection ? category.selection.index : 0;
        state.visible = [];
        library.removeAll();
        for (var i = 0; i < DATA.items.length; i++) {
            var item = DATA.items[i];
            if ((!cat || item.category === cat - 1) && item.name.toLowerCase().indexOf(query) >= 0) {
                state.visible.push(item);
                library.add("item", ("00" + item.id).slice(-3) + "  " + item.name);
            }
        }
        apply.enabled = state.visible.length > 0;
        status.text = state.visible.length + " efeitos encontrados.\nPrévia mostra a receita original.";
        if (state.visible.length) { library.selection = 0; select(); }
        else { state.current = null; selectedName.text = "Nenhum efeito encontrado"; preview.image = null; }
    }
    function number(text, label, min, max) {
        var s = String(text).replace(",", ".").replace(/^\s+|\s+$/g, "");
        var value = Number(s);
        if (!s || !isFinite(value) || value < min || value > max) throw new Error(label + ": use um número entre " + min + " e " + max + ".");
        return value;
    }
    function selectionPivot(comp, layers) {
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        var ids = {};
        for (var i = 0; i < layers.length; i++) ids[layers[i].id] = true;
        for (i = 1; i <= comp.numLayers; i++) {
            var l = comp.layer(i);
            var parent = l.parent;
            var matte = l instanceof AVLayer ? l.trackMatteLayer : null;
            if (parent && !!ids[l.id] !== !!ids[parent.id] || matte && !!ids[l.id] !== !!ids[matte.id])
                throw new Error("Inclua na seleção as camadas conectadas por parenting ou track matte.");
        }
        for (i = 0; i < layers.length; i++) {
            l = layers[i];
            if (!(l instanceof AVLayer) || l.locked || l.threeDLayer || l.adjustmentLayer)
                throw new Error("Selecione camadas 2D desbloqueadas, sem camadas de ajuste.");
            var r = l.sourceRectAtTime(comp.time, true);
            var corners = [[r.left,r.top],[r.left+r.width,r.top],[r.left,r.top+r.height],[r.left+r.width,r.top+r.height]];
            for (var k = 0; k < corners.length; k++) {
                var p = l.sourcePointToComp(corners[k]);
                minX = Math.min(minX,p[0]); maxX = Math.max(maxX,p[0]);
                minY = Math.min(minY,p[1]); maxY = Math.max(maxY,p[1]);
            }
        }
        if (!isFinite(minX + maxX + minY + maxY)) throw new Error("Não foi possível calcular os limites da seleção.");
        return [(minX+maxX)/2, (minY+maxY)/2];
    }
    function documentFor(item, ratio, amount, pivot, comp) {
        var doc = {effectcraftAnimationPreset: 2, name: "IGPACK " + item.name, properties: [], effects: []};
        var px = "thisComp.width*" + (pivot[0]/comp.width);
        var py = "thisComp.height*" + (pivot[1]/comp.height);
        for (var i = 0; i < item.effects.length; i++) {
            var recipe = item.effects[i];
            var g = clone(DATA.groups[recipe.id]);
            walk(g,"",function (path,p) {
                if (recipe.changes[path]) {
                    var change = recipe.changes[path];
                    p.value = clone(change.value);
                    if (change.keys) p.keys = clone(change.keys);
                    if (change.expr) p.expr = clone(change.expr);
                }
                var kind = p.value.t;
                function adjust(v) {
                    if (path === "opacity" || kind === "Bool" || kind === "Enum" || kind === "Str" || path === "anchor") return v;
                    if (kind === "Vec2") return [v[0]*amount,v[1]*amount];
                    if (path === "scaleHeight" || path === "scaleWidth") return Math.max(0,100+(v-100)*amount);
                    return v*amount;
                }
                if (p.keys && p.keys.length) {
                    for (var k = 0; k < p.keys.length; k++) {
                        p.keys[k].time = Math.round(p.keys[k].time*ratio);
                        p.keys[k].value.v = adjust(p.keys[k].value.v);
                    }
                    p.value = clone(p.keys[0].value);
                } else if (g.kind.effect === "ec.stylize.glow" && path === "intensity") p.value.v *= amount;
                if (p.expr && p.expr.enabled) {
                    p.expr.text = p.expr.text.replace(/time-key\(1\).time/g,"((time-key(1).time)/"+ratio+")");
                    if (path === "rotation" && p.expr.text.indexOf("var d=") >= 0) {
                        var split = p.expr.text.lastIndexOf(";");
                        p.expr.text = p.expr.text.slice(0,split+1)+" ("+p.expr.text.slice(split+1)+")*"+amount;
                    }
                }
                if (g.kind.effect === "ec.distort.transform") {
                    if (path === "anchor") p.expr = {enabled:true,text:"["+px+","+py+"]"};
                    if (path === "position") {
                        var body;
                        if (p.expr && p.expr.text.indexOf("var d=") >= 0) {
                            body = p.expr.text.replace(/thisLayer.width\/2/g,px).replace(/thisLayer.height\/2/g,py);
                            body = body.replace("; [", "; a*="+amount+"; [");
                        } else if (p.keys && p.keys.length) body="["+px+"+value[0]*thisComp.width,"+py+"+value[1]*thisComp.height]";
                        else body="["+px+","+py+"]";
                        p.expr = {enabled:true,text:body};
                    }
                }
            });
            doc.effects.push(g);
        }
        return doc;
    }
    function addEffect() {
        var started = false, edited = false;
        var previousTime, comp;
        try {
            if (app.buildName !== "0.21.0") throw new Error("Este painel exige EffectCraft 0.21.0.");
            comp = app.project.activeItem;
            if (!(comp instanceof CompItem)) throw new Error("Abra uma composição antes de adicionar um efeito.");
            if (!state.current) throw new Error("Escolha um efeito.");
            var d = number(duration.text,"Duração",1/comp.frameRate,30);
            d = Math.max(1,Math.round(d*comp.frameRate))/comp.frameRate;
            var amount = number(strength.text,"Intensidade",0,200)/100;
            var start = comp.time;
            if (start+d > comp.duration+0.000001) throw new Error("A animação não cabe após o cursor. Reduza a duração ou mova o cursor.");
            var precompose = mode.selection && mode.selection.index === 1;
            var selected = comp.selectedLayers;
            if (precompose && !selected.length) throw new Error("Selecione as camadas que deseja animar.");
            var pivot = precompose ? selectionPivot(comp,selected) : [comp.width/2,comp.height/2];
            var doc = documentFor(state.current,d/state.current.duration,amount,pivot,comp);
            previousTime = start;
            app.beginUndoGroup("IGPACK - "+state.current.name); started = true;
            var layer;
            if (precompose) {
                var indices = [];
                for (var i = 0; i < selected.length; i++) indices.push(selected[i].index);
                comp.layers.precompose(indices,"IGPACK - "+state.current.name,true); edited = true;
                layer = comp.selectedLayers[0];
            } else {
                var asset = app.project.items.addComp("IGPACK FX - "+state.current.name,comp.width,comp.height,comp.pixelAspect,d,comp.frameRate); edited = true;
                asset.layers.addSolid([1,1,1],"Cobertura do efeito",comp.width,comp.height,comp.pixelAspect,d);
                layer = comp.layers.add(asset);
                layer.name = "IGPACK - "+state.current.name;
                layer.adjustmentLayer = true;
                layer.startTime = start;
                layer.inPoint = start;
                layer.outPoint = start+d;
                layer.moveToBeginning();
            }
            app.run("comp.open",{comp:comp.id});
            app.run("time.set",{time:start});
            var result = app.run("anim.applyPreset",{layers:[layer.id],preset:doc});
            if (result.skipped.length || result.applied !== doc.effects.length) throw new Error("Aplicação incompleta; a operação será desfeita.");
            layer.comment = "IGPACK Motion Browser | "+state.current.id+" | "+d+" s | "+Math.round(amount*100)+"%";
            app.run("layer.select",{layers:[layer.id]});
            app.endUndoGroup(); started = false;
            IGPACK_MOTION.lastResult = {layer:layer.id,comp:comp.id,preset:state.current.id,duration:d,overlay:!precompose};
            status.text = "Adicionado: "+state.current.name+"\n"+d+" s · "+Math.round(amount*100)+"%\n"+(precompose ? "Abra a precomp para editar." : "Mova o clipe para posicionar.");
        } catch (e) {
            if (started) app.endUndoGroup();
            if (edited) app.executeCommand(app.findMenuCommandId("Undo"));
            if (comp && previousTime !== undefined) {
                app.run("comp.open",{comp:comp.id}); app.run("time.set",{time:previousTime});
                if (edited && selected) {
                    var originalIds = [];
                    for (var j = 0; j < selected.length; j++) originalIds.push(selected[j].id);
                    app.run("layer.select",{layers:originalIds});
                }
            }
            status.text = "Não aplicado: "+e.message;
        }
    }
    IGPACK_MOTION = {tick:tick,lastResult:null};
    // Docked panels run inside a host wrapper; timer strings execute in the global scope.
    $.global.IGPACK_MOTION = IGPACK_MOTION;
    library.onChange = select;
    search.onChanging = filter;
    search.onChange = filter;
    category.onChange = filter;
    mode.onChange = modeChanged;
    apply.onClick = addEffect;
    play.onClick = function () { state.playing = !state.playing; play.text = state.playing ? "Pausar preview" : "Reproduzir preview"; };
    ui.onClose = function () { if (state.task !== null) app.cancelTask(state.task); };
    function responsive() {
        var width = Math.max(220,ui.size[0]-32);
        var narrow = width < 600;
        filters.orientation = narrow ? "column" : "row";
        controls.orientation = narrow ? "column" : "row";
        controls.alignChildren = ["left","top"];
        filters.alignChildren = ["fill","top"];
        body.orientation = narrow ? "column" : "row";
        search.preferredSize = [narrow ? width : 310,28];
        category.preferredSize = [narrow ? width : 270,28];
        library.preferredSize = [narrow ? width : 255,narrow ? 140 : 400];
        right.preferredSize = [narrow ? width : 350,narrow ? 465 : 400];
        preview.preferredSize = [Math.min(320,width),Math.min(180,width*9/16)];
        note.preferredSize = [narrow ? width : 340,44];
        apply.preferredSize = [narrow ? width : 340,32];
        status.preferredSize = [width,46];
        ui.layout.layout(true);
    }
    ui.onResize = responsive;
    ui.onResizing = responsive;
    filter();
    state.task = app.scheduleTask("IGPACK_MOTION.tick()",67,true);
    if (ui instanceof Window) ui.show(); else ui.layout.layout(true);
})(this);
