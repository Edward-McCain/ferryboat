<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  crossing: {
    type: Object,
    default: null,
  },
  error: {
    type: String,
    default: "",
  },
  pending: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["save", "close"]);

const departure = ref("21:40");
const berth = ref(1);
const direction = ref("city_to_island");
const capacity = ref(40);
const note = ref("");

watch(
  () => props.crossing,
  (crossing) => {
    departure.value = crossing?.departure ?? "21:40";
    berth.value = crossing?.berth ?? 1;
    direction.value = crossing?.direction ?? "city_to_island";
    capacity.value = crossing?.capacity ?? 40;
    note.value = crossing?.note ?? "";
  },
  { immediate: true },
);

function submit() {
  emit("save", {
    departure: departure.value,
    berth: Number(berth.value),
    direction: direction.value,
    capacity: Number(capacity.value),
    note: note.value,
  });
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <h2>{{ crossing ? "Поправка" : "Новый рейс" }}</h2>
    <p v-if="error" class="alert" role="alert">{{ error }}</p>

    <label class="field">
      <span>Время отхода</span>
      <input v-model="departure" class="time-field" inputmode="numeric" maxlength="5" required />
    </label>

    <fieldset class="field">
      <legend>Причал</legend>
      <div class="plaques">
        <label v-for="number in [1, 2, 3, 4]" :key="number" class="plaque">
          <input v-model="berth" type="radio" name="berth" :value="number" />
          <span>{{ number }}</span>
        </label>
      </div>
    </fieldset>

    <fieldset class="field">
      <legend>Куда</legend>
      <div class="directions">
        <label class="direction">
          <input v-model="direction" type="radio" name="direction" value="city_to_island" />
          <span>Город</span>
          <span class="route-line" aria-hidden="true"></span>
          <span>Остров</span>
        </label>
        <label class="direction">
          <input v-model="direction" type="radio" name="direction" value="island_to_city" />
          <span>Остров</span>
          <span class="route-line" aria-hidden="true"></span>
          <span>Город</span>
        </label>
      </div>
    </fieldset>

    <label class="field">
      <span>Места</span>
      <input v-model="capacity" class="number-field" type="number" min="1" max="80" required />
    </label>

    <label class="field">
      <span>Пометка</span>
      <textarea v-model="note" rows="3" maxlength="280"></textarea>
    </label>

    <div class="form-actions">
      <button type="submit" class="solid" :disabled="pending">
        {{ pending ? "Записываю…" : crossing ? "Сохранить поправки" : "Поставить в расписание" }}
      </button>
      <button type="button" class="text-button" :disabled="pending" @click="emit('close')">
        К листу
      </button>
    </div>
  </form>
</template>
