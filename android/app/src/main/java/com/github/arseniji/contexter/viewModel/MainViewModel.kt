package com.github.arseniji.contexter.viewModel

import androidx.lifecycle.ViewModel
import com.github.arseniji.contexter.dataClasses.AnswerItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlin.collections.emptyList

class MainViewModel : ViewModel(){
    private val _answers = MutableStateFlow<List<AnswerItem>>(emptyList())
    val answers: StateFlow<List<AnswerItem>> = _answers.asStateFlow()
    fun addAnswer(){

    }
}