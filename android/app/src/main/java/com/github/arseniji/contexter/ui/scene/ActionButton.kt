package com.github.arseniji.contexter.ui.scene

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.QuestionMark
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.github.arseniji.contexter.enums.ActionButtonTypes

@Composable
fun ActionButton(
    modifier: Modifier = Modifier,
    type: ActionButtonTypes,
    onButtonClick: () -> Unit
) {
    val icon = when (type) {
        ActionButtonTypes.hintButton -> Icons.Default.Lightbulb
        ActionButtonTypes.answerButton -> Icons.Default.QuestionMark
    }

    val backgroundColor = when (type) {
        ActionButtonTypes.hintButton -> Color(0xffff5d00)
        ActionButtonTypes.answerButton -> Color(0xff007d2a)
    }

    val contentColor = Color.White

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = backgroundColor,
        onClick = onButtonClick
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = type.name,
                tint = contentColor,
                modifier = Modifier.size(24.dp)
            )
            Text(
                text = type.label,
                color = contentColor,
                modifier = Modifier.padding(top = 4.dp)
            )
        }
    }
}