package com.github.arseniji.contexter.enums;

public enum ActionButtonTypes {
    hintButton("Подсказка"),
    answerButton("Ответ");
    private final String label;
    ActionButtonTypes(String str){
        this.label = str;
    }
    public String getLabel(){
        return label;
    }
}
