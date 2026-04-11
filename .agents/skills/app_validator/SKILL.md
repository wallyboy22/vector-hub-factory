---
name: app_validator
description: Skill to validate and compare apps in the vector-hub-factory project — checking layout fidelity against the HTML reference (references/mapbiomas-chat), RAG pipeline correctness and PDF navigation.
---

# App Validator Skill

This skill provides a systematic way to validate that Streamlit apps in `vector-hub-factory`
maintain visual and functional parity with the HTML reference in `references/mapbiomas-chat/`.

## Reference Design
The HTML interface at `references/mapbiomas-chat/ui/index.html` is the **visual standard**.
All Streamlit apps must replicate its layout, proportions and behavior.

## Components

1. **Server Check**: Ensures the Streamlit app is running on the expected port.
2. **Visual Comparison**: Checklist against the HTML reference.
3. **Functional Test**: Verification of the RAG pipeline and PDF navigation.
4. **Style Guide Compliance**: Check against `vector_hub_factory` skill section 6.

## Instructions

### 1. Verification of Ports
Run the following command to check if Streamlit is running:
```powershell
netstat -ano | findstr :8501
```

### 2. Layout Checklist (vs HTML Reference)
Open the Streamlit app and the HTML reference side-by-side and verify:
- [ ] **Split Screen**: Left column (Chat) ~30%, right column (PDF) ~70%.
- [ ] **Header**: Logo and title text same size and position as HTML reference.
- [ ] **Document Tabs**: All registered documents show as tabs or selectors.
- [ ] **Colors**: Primary color matches the document's `color` in `config.py`.
- [ ] **No Streamlit boxes**: No visible padding/margin from native Streamlit containers.

### 3. Functional Checklist
- [ ] **Question Input**: Typing a question and pressing Enter triggers a response.
- [ ] **Suggestions Drawer**: Chips open upward and close on selection.
- [ ] **PDF Loading**: PDF content is visible and scrollable.
- [ ] **PDF Navigation**: Clicking a "p. X" source tag jumps the PDF to that page.
- [ ] **RAG Pipeline**: Response cites at least one page number from the document.

## Troubleshooting

- **PDF not loading**: Ensure the FastAPI server is running at port 8000, as the Streamlit app may proxy PDF requests there for better performance.
- **NameError**: Check for typos in `app.py`, especially `LLM_MODELS` vs `LL_MODELS`.
- **CSS Issues**: Check if `st.markdown(unsafe_allow_html=True)` is used correctly.
