import katex from "katex";
import renderMathInElement from "katex/contrib/auto-render";
import "katex/dist/katex.min.css";

/**
 * Safely render a LaTeX math expression using KaTeX.
 * Strips internal newlines to prevent Markdown block/list parsing disruptions.
 */
export function renderMathSafe(math, isDisplay) {
  const clean = math.trim();
  if (!clean) return "";
  try {
    const rendered = katex.renderToString(clean, {
      displayMode: isDisplay,
      throwOnError: false,
      errorColor: "#cc0000",
      strict: "ignore",
    });
    // Strip newlines so Markdown block parsers (lists, tables) are not disrupted
    const inlineSafe = rendered.replace(/\r?\n\s*/g, " ");
    if (isDisplay) {
      return "\n\n<div class=\"katex-display-wrapper\">" + inlineSafe + "</div>\n\n";
    }
    return inlineSafe;
  } catch (err) {
    console.error("[KaTeX Render Error]", err);
    return isDisplay ? "\n\n$$ " + math + " $$\n\n" : "$" + math + "$";
  }
}

/**
 * Comprehensive preprocessor for LaTeX mathematical expressions in Markdown.
 * Supports:
 * - Block math: ```math ... ```, ```latex ... ```, ```katex ... ```
 * - Display math: $$ ... $$ and \[ ... \]
 * - Inline math: \( ... \) and $ ... $
 * Fully compatible with lists, tables, Chinese characters, and accents.
 */
export function preprocessMath(md) {
  if (!md || typeof md !== "string") return md;

  try {
    const codePlaceholders = [];

    // 1. First extract and render math code blocks (```math ... ```, ```latex ... ```, ```katex ... ```)
    let text = md.replace(/```(?:math|katex|latex)[\r\n]+([\s\S]+?)```/gi, function (_, math) {
      return renderMathSafe(math, true);
    });

    // 2. Protect remaining code blocks (```...``` or ~~~...~~~)
    text = text.replace(/(```[\s\S]*?```|~~~[\s\S]*?~~~)/g, function (match) {
      const ph = "@@FN_CODE_FENCE_" + codePlaceholders.length + "@@";
      codePlaceholders.push({ ph, code: match });
      return ph;
    });

    // 3. Protect inline code (`...`)
    text = text.replace(/(`[^`\n]+?`)/g, function (match) {
      const ph = "@@FN_CODE_INLINE_" + codePlaceholders.length + "@@";
      codePlaceholders.push({ ph, code: match });
      return ph;
    });

    // 4. Render display math: $$ ... $$
    text = text.replace(/\$\$([\s\S]+?)\$\$/g, function (_, math) {
      return renderMathSafe(math, true);
    });

    // 5. Render display math: \[ ... \]
    text = text.replace(/\\\[([\s\S]+?)\\\]/g, function (_, math) {
      return renderMathSafe(math, true);
    });

    // 6. Render inline math: \( ... \)
    text = text.replace(/\\\(([\s\S]+?)\\\)/g, function (_, math) {
      return renderMathSafe(math, false);
    });

    // 7. Render inline math: $ ... $
    // Match single $ that is not escaped (\$) and not part of $$
    text = text.replace(/(?<!\\|\$)\$(?!\$)([^\$\n]+?)(?<!\\|\$)\$(?!\$)/g, function (_, math) {
      return renderMathSafe(math, false);
    });

    // 8. Restore protected code blocks
    for (let i = codePlaceholders.length - 1; i >= 0; i--) {
      text = text.replace(codePlaceholders[i].ph, codePlaceholders[i].code);
    }

    return text;
  } catch (err) {
    console.error("[preprocessMath error]", err);
    return md;
  }
}

/**
 * Secondary safety net: renders any unparsed LaTeX formulas directly within DOM tree.
 */
export function renderMathInDOM(container) {
  if (!container) return;
  try {
    renderMathInElement(container, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false },
        { left: "$", right: "$", display: false },
      ],
      throwOnError: false,
      errorColor: "#cc0000",
      strict: "ignore",
    });
  } catch (err) {
    console.warn("[renderMathInDOM error]", err);
  }
}
