package com.github.arseniji.contexter.dataClasses

import androidx.compose.ui.graphics.Color

data class AnswerItem(
    val word: String, val rank: Int
) {
    fun getColor(): Color {
        return when {
            rank <= 100 -> Color.Green
            rank  <= 500 -> Color.Yellow
            else -> Color.Red
        }
    }
}
