"""Readable source and measurement view; raw trace remains separately available."""
import json
import streamlit as st

SECTION_LABELS = {
    'ingredients':'Ingredients', 'ingredient_notes':'Ingredient notes',
    'instructions':'Preparation', 'overview':'Recipe overview',
    'dietary':'Source dietary tags', 'recipe':'Full recipe',
}


def ingredient_lines(text):
    """Parse only an ingredients section; return None when it isn't valid JSON."""
    marker='\ningredients: '
    if marker not in text:
        return None
    try:
        items=json.loads(text.split(marker,1)[1])
        if not isinstance(items,list):return None
        lines=[]
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('name'),str):return None
            amount=item.get('quantity')
            unit=item.get('unit') or ''
            value=f'{amount:g} {unit}'.strip() if isinstance(amount,(int,float)) and not isinstance(amount,bool) else 'to taste' if unit=='toTaste' else 'amount not specified'
            note=item.get('note') or ''
            lines.append(f"{item['name']}: {value}"+(f' — {note}' if note else ''))
        return lines
    except (ValueError,TypeError):
        return None


def readable_body(chunk):
    text=str(chunk.get('text') or '')
    if chunk.get('metadata',{}).get('section')=='ingredients':
        lines=ingredient_lines(text)
        if lines is not None:return '\n'.join('• '+line for line in lines)
    # Section headers appear in the heading; keep the actual content intact.
    return text.split('\n',1)[1].split(': ',1)[1] if '\n' in text and ': ' in text.split('\n',1)[1] else text


def render_details(details):
    """Render one assistant message's trace identically on initial and later reruns."""
    chunks=details.get('retrieved_chunks') or []
    with st.expander('Sources and measurements'):
        if chunks:
            st.markdown('**Recipe sources**')
            st.caption('Recipe data: UniTools · CC BY-SA 4.0')
            st.markdown('[Open the UniTools dataset](https://theunitools.com/en/data)')
            st.caption('Source information and dietary tags have not been independently verified.')
            # Put the record used by the answer first for reading; the raw trace
            # below retains the original retrieval order and scores.
            display_chunks=sorted(chunks,key=lambda c: 0 if (c.get('metadata') or {}).get('evidence_type')=='structured_lookup' else 1)
            for chunk in display_chunks:
                meta=chunk.get('metadata') or {}
                name=str(meta.get('recipe') or 'Recipe')
                section=SECTION_LABELS.get(meta.get('section'),str(meta.get('section') or 'Source'))
                origin='Stored recipe record' if meta.get('evidence_type')=='structured_lookup' else 'Search result'
                st.markdown(f'**{name} · {section}**')
                st.caption(origin)
                st.text(readable_body(chunk))
        else:
            st.write('No recipe sources were used for this reply.')

        call=details.get('mcp_call') or {}
        if call:
            st.markdown('**Calculation**')
            args=call.get('arguments') or {}
            if call.get('name')=='scale_recipe':
                st.write(f"Scaled from {args.get('from_servings', '?')} to {args.get('to_servings', '?')} servings.")
            elif call.get('name')=='convert_units':
                st.write(f"Converted {args.get('amount', '?')} {args.get('from_unit', '')} to {args.get('to_unit', '')}.")
            else:
                st.write('A calculation tool was used.')
        st.markdown('**Measurements**')
        seconds=details.get('total_seconds')
        st.write(f'Response time: {seconds:g} seconds' if isinstance(seconds,(int,float)) else 'Response time: unavailable')
        ins,outs=details.get('total_input_tokens'),details.get('total_output_tokens')
        if ins is not None and outs is not None:
            st.write(f'Model tokens: {ins} input, {outs} output (safety checks excluded).')
        else:
            st.caption('Token counts are unavailable for this reply; safety checks are excluded.')

    with st.expander('Debug: complete raw trace'):
        st.caption('Detailed source chunks, tool calls and measurements for troubleshooting.')
        st.json(details)
