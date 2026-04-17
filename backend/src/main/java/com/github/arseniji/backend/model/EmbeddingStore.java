package com.github.arseniji.backend.model;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Scanner;
import java.util.stream.IntStream;

public class EmbeddingStore {

    private final MappedByteBuffer embeddingsBuffer;
    private final int[] popularIndices;
    private final List<String> vocab;
    private final List<String> popularWords;
    private final Map<String, Integer> wordToIndexMap;
    private static final int DIM = 300;
    private static final int BYTES_PER_VEC = DIM * 4;
    public EmbeddingStore(Path embPath, Path popIdxPath, Path vocabPath, Path popWordsPath) throws IOException {
        try (FileChannel ch = FileChannel.open(embPath, StandardOpenOption.READ)) {
            embeddingsBuffer = ch.map(FileChannel.MapMode.READ_ONLY, 0, ch.size());
            embeddingsBuffer.order(ByteOrder.LITTLE_ENDIAN);
        }

        try (FileChannel ch = FileChannel.open(popIdxPath, StandardOpenOption.READ)) {
            int count = (int) (ch.size() / 4);
            MappedByteBuffer buf = ch.map(FileChannel.MapMode.READ_ONLY, 0, ch.size());
            buf.order(ByteOrder.LITTLE_ENDIAN);
            popularIndices = new int[count];
            buf.asIntBuffer().get(popularIndices);
        }

        vocab = Files.readAllLines(vocabPath, StandardCharsets.UTF_8);
        popularWords = Files.readAllLines(popWordsPath, StandardCharsets.UTF_8);

        wordToIndexMap = new java.util.HashMap<>();
        for (int i = 0; i < vocab.size(); i++) {
            wordToIndexMap.put(vocab.get(i), i);
        }
    }

    public float[] getEmbedding(int vocabIndex) {
        float[] vec = new float[DIM];
        int byteOffset = vocabIndex * BYTES_PER_VEC;
        for (int i = 0; i < DIM; i++) {
            vec[i] = embeddingsBuffer.getFloat(byteOffset + i * 4);
        }
        return vec;
    }
    public int getPopularCount() { return popularIndices.length; }
    public static double dotProduct(float[] vecA, float[] vecB) {
        double sum = 0.0;
        for (int i = 0; i < vecA.length; i++) {
            sum += vecA[i] * vecB[i];
        }
        return sum;
    }

    public int getRank(String secretWord, String targetWord) {
        int secretIdx = findVocabIndex(secretWord);
        int targetIdx = findVocabIndex(targetWord);
        if (secretIdx == -1 || targetIdx == -1) {
            return -1; 
        }
        float[] secretVec = getEmbedding(secretIdx);
        float[] targetVec = getEmbedding(targetIdx);
        double targetSim = dotProduct(secretVec, targetVec);
        int rank = 1;
        for (int popVocabIdx : popularIndices) {
            if (popVocabIdx == targetIdx) continue;
            float[] popVec = getEmbedding(popVocabIdx);
            double popSim = dotProduct(secretVec, popVec);
            if (popSim > targetSim) {
                rank++;
            }
        }

        return rank;
    }

    private int findVocabIndex(String word) {
        return wordToIndexMap.getOrDefault(word.toLowerCase(), -1);
    }

    static void main(String[] args) throws IOException {
        
        Path base = Path.of("..", "java_datasets").toAbsolutePath().normalize();
        EmbeddingStore store = new EmbeddingStore(
                base.resolve("embeddings.bin"),
                base.resolve("popular_indices.bin"),
                base.resolve("vocab.txt"),
                base.resolve("popular_words.txt")
        );
        Random random = new Random();
        int secretPopularIndex = random.nextInt(store.getPopularCount());
        String secretWord = store.popularWords.get(secretPopularIndex);

        System.out.println("SECRET WORD IS: " + secretWord);

        System.out.println("--- Welcome to Contexto Clone ---");
        System.out.println("Guess the secret word!");
        System.out.println("Enter words in Russian (lowercase). Type 'exit' to quit.");
        Scanner scanner = new Scanner(System.in);

        while (true) {
            System.out.print("> ");
            String input = scanner.nextLine().trim().toLowerCase();

            if (input.equals("exit")) break;
            if (input.isEmpty()) continue;

            if (store.findVocabIndex(input) == -1) {
                System.out.println("Word not found in dictionary.");
                continue;
            }

            int rank = store.getRank(secretWord, input);

            if (rank == -1) {
                System.out.println("Error calculating rank.");
            } else if (rank == 1) {
                System.out.println("🎉 CORRECT! The word was '" + secretWord + "'!");
                System.out.println("Play again? Restart the application.");
                break;
            } else {
                System.out.println("Rank: " + rank);

                
                if (rank <= 10) System.out.println("🔥 Very hot!");
                else if (rank <= 100) System.out.println("Hot");
                else if (rank <= 1000) System.out.println("Warm");
                else System.out.println("Cold");
            }
        }
        scanner.close();
    }
}