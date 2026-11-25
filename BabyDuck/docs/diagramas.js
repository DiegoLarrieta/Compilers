/* Dibuja diagramas de sintaxis a partir de una notación tipo EBNF escrita
   dentro de cada <div class="rr" data-rule="NOMBRE">:
     'x'            terminal            NOMBRE        no terminal
     @n             punto neurálgico    ( a | b )     alternativas
     [ a ]          opcional            { a }         cero o más
     { a }+         uno o más           { a / s }+    uno o más separados por s */
(function () {
  var esc = function (s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };
  var VACIO = { k: "seq", s: [] };

  function parse(src) {
    var t = src.match(/'[^']*'|@\w+|[\[\]{}()|\/+]|[^\s'@\[\]{}()|\/+]+/g) || [], i = 0;
    function alt() {
      var a = [seq()];
      while (t[i] === "|") { i++; a.push(seq()); }
      return a.length > 1 ? { k: "alt", a: a } : a[0];
    }
    function seq() {
      var s = [];
      while (i < t.length && !/^[\]})|\/]$/.test(t[i])) s.push(item());
      return s.length === 1 ? s[0] : { k: "seq", s: s };
    }
    function item() {
      var x = t[i++], a, r, sep = null;
      if (x === "[") { a = alt(); i++; return { k: "alt", a: [a, VACIO] }; }
      if (x === "(") { a = alt(); i++; return a; }
      if (x === "{") {
        a = alt();
        if (t[i] === "/") { i++; sep = alt(); }
        i++;
        r = { k: "rep", a: a, sep: sep };
        if (t[i] === "+") { i++; return r; }
        return { k: "alt", a: [r, VACIO] };
      }
      if (x[0] === "'") return { k: "t", v: x.slice(1, -1) };
      if (x[0] === "@") return { k: "p", v: x.slice(1) };
      return { k: "n", v: x };
    }
    return alt();
  }

  var LN = '<i class="rr-ln"></i>', FILL = '<i class="rr-ln rr-fill"></i>';
  function fila(n, clase) {
    var dentro = n.k === "seq" && !n.s.length ? "" : LN + dibuja(n);
    return '<span class="rr-row' + (clase || "") + '">' + dentro + FILL + "</span>";
  }
  function dibuja(n) {
    if (n.k === "t") return '<span class="rr-t">' + esc(n.v) + "</span>";
    if (n.k === "n") return '<span class="rr-n">' + esc(n.v) + "</span>";
    if (n.k === "p") return '<span class="rr-p' + (/^S/.test(n.v) ? " rr-ps" : (Number(n.v) >= 17 ? " rr-pn" : "")) + '" title="punto neurálgico ' + esc(n.v) + '">' + esc(n.v) + "</span>";
    if (n.k === "seq") return '<span class="rr-seq">' + n.s.map(dibuja).join(LN) + "</span>";
    if (n.k === "alt") return '<span class="rr-alt">' + n.a.map(function (a) { return fila(a); }).join("") + "</span>";
    var regreso = '<span class="rr-row rr-back">' + LN + '<span class="rr-loop" title="se repite">↺</span>' + (n.sep ? LN + dibuja(n.sep) : "") + FILL + "</span>";
    return '<span class="rr-alt">' + fila(n.a) + regreso + "</span>";
  }

  document.querySelectorAll(".rr").forEach(function (el) {
    var arbol = parse(el.textContent);
    el.innerHTML = '<span class="rr-name">' + esc(el.dataset.rule) + '</span><span class="rr-body"><span class="rr-dot"></span>' +
      LN + dibuja(arbol) + LN + '<span class="rr-dot"></span></span>';
  });
})();
